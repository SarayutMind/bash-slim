#!/usr/bin/env bash
# bash-slim check runner: one short command in, one line out.
#
#   check.sh                        fix + typecheck (whichever this project has)
#   check.sh typecheck build test   any package.json script, by name
#   check.sh fix                    biome / prettier / eslint --write on changed files only
#   check.sh 'api=yarn workspace @repo/api typecheck'    custom step: name=command
#
# Success prints one line:   ✅ fix · ✅ typecheck (41s)
# Failure prints that line, then the error lines of each failed step and the
# path of its full log. Exit code is 1 when any step fails.
# Env: BASH_SLIM_LINES (default 40) = max log lines printed per failed step.

set -u
max=${BASH_SLIM_LINES:-40}

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$root" || exit 2

if [ -f yarn.lock ]; then pm=yarn
elif [ -f pnpm-lock.yaml ]; then pm=pnpm
elif [ -f bun.lockb ] || [ -f bun.lock ]; then pm=bun
else pm=npm; fi

run_script() { case $pm in npm) npm run -s "$1" ;; *) "$pm" run "$1" ;; esac; }
pm_exec() {
  case $pm in
    yarn) yarn "$@" ;;
    pnpm) pnpm exec "$@" ;;
    bun) bunx "$@" ;;
    npm) npx --no-install "$@" ;;
  esac
}

scripts=" "
[ -f package.json ] && scripts=" $(node -e 'process.stdout.write(Object.keys(require("./package.json").scripts||{}).join(" "))' 2>/dev/null) "
has_script() { case "$scripts" in *" $1 "*) return 0 ;; esac; return 1; }

has_biome() { [ -f biome.json ] || [ -f biome.jsonc ]; }
has_prettier() { ls .prettierrc* prettier.config.* >/dev/null 2>&1; }
has_eslint() { ls .eslintrc* eslint.config.* >/dev/null 2>&1; }

# fix: format + lint only the files changed since HEAD (tracked and new), like lint-staged.
SKIP=99
step_fix() {
  local files=() js=() f
  while IFS= read -r -d '' f; do [ -f "$f" ] && files+=("$f"); done < <(
    git diff -z --name-only HEAD 2>/dev/null
    git ls-files -z --others --exclude-standard 2>/dev/null
  )
  [ ${#files[@]} -eq 0 ] && return $SKIP
  if has_biome; then
    pm_exec biome check --write --no-errors-on-unmatched --files-ignore-unknown=true "${files[@]}"
    return
  fi
  local ran=0
  if has_prettier; then pm_exec prettier --write --ignore-unknown "${files[@]}" || return 1; ran=1; fi
  if has_eslint; then
    for f in "${files[@]}"; do
      case $f in *.js | *.jsx | *.mjs | *.cjs | *.ts | *.tsx | *.vue) js+=("$f") ;; esac
    done
    if [ ${#js[@]} -gt 0 ]; then pm_exec eslint --fix "${js[@]}" || return 1; fi
    ran=1
  fi
  [ $ran = 1 ] || { echo "no biome, prettier or eslint config found"; return 1; }
}

steps=("$@")
if [ ${#steps[@]} -eq 0 ]; then
  { has_biome || has_prettier || has_eslint; } && steps+=(fix)
  has_script typecheck && steps+=(typecheck)
  [ ${#steps[@]} -eq 0 ] && { echo "check.sh: nothing to run here; pass step names (see --help)"; exit 2; }
fi
case ${steps[0]} in -h | --help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

logdir="${TMPDIR:-/tmp}/bash-slim"
mkdir -p "$logdir"
summary=()
failed=()
start=$SECONDS

for step in "${steps[@]}"; do
  name=${step%%=*}
  cmd=""
  [ "$name" != "$step" ] && cmd=${step#*=}
  log="$logdir/$(printf %s "$name" | tr -c 'A-Za-z0-9_-' '_').log"
  if [ -n "$cmd" ]; then bash -c "$cmd" >"$log" 2>&1
  elif [ "$name" = fix ]; then step_fix >"$log" 2>&1
  elif has_script "$name"; then run_script "$name" >"$log" 2>&1
  else echo "no \"$name\" script in package.json" >"$log"; false; fi
  rc=$?
  if [ $rc -eq 0 ]; then summary+=("✅ $name"); [ "$name" = fix ] && fix_ok=1
  elif [ $rc -eq $SKIP ]; then summary+=("– $name (no changed files)")
  else summary+=("❌ $name"); failed+=("$name|$log"); fi
done

line=""
for s in "${summary[@]}"; do line="${line:+$line · }$s"; done
echo "$line ($((SECONDS - start))s)"

# For each failed step print, in this order:
#   1. the errors: biome diagnostics grouped by rule when there are many, otherwise
#      the error lines (+2 lines of context), or the last lines if nothing matches
#   2. the tool's own summary lines (Found 444 errors, Tasks:, Failed:, ...)
#   3. whether any file you changed appears in the log, so pre-existing errors are obvious
#   4. where the full log lives
pat='error|Error|ERR!|✖|×|FAIL|failed|Failed|panic|Exception|━━'
sumpat='^ *(Found [0-9]+|Checked [0-9]+|Diagnostics not shown|Tasks: |Failed: |Tests? .*[0-9]+ (failed|passed))'
changed=()
while IFS= read -r f; do [ -n "$f" ] && changed+=("$f"); done < <(
  git diff --name-only HEAD 2>/dev/null
  git ls-files --others --exclude-standard 2>/dev/null
)
for entry in "${failed[@]+"${failed[@]}"}"; do
  name=${entry%%|*}
  log=${entry#*|}
  clean=$(sed -E $'s/\x1b\\[[0-9;?]*[A-Za-z]//g; s/\r$//' "$log" |
    grep -v -E '^warning: in the working copy of|LF will be replaced by CRLF|^[[:space:]]*$')
  heads=$(printf '%s\n' "$clean" | awk '/━━/ && $2 !~ /^━/ && NF > 2')
  nheads=$(printf '%s' "$heads" | grep -c '' || true)
  if [ "$nheads" -gt 3 ]; then
    errs=$(printf '%s\n' "$heads" | awk '{c=$2; n[c]++; if (n[c] <= 2) ex[c] = ex[c] (n[c] > 1 ? ", " : "") $1}
      END {for (c in n) printf "%s ×%d (%s%s)\n", c, n[c], ex[c], (n[c] > 2 ? ", …" : "")}')
  else
    errs=$(printf '%s\n' "$clean" | grep -E -A2 "$pat" | grep -v -x -e '--')
    [ -n "$errs" ] || errs=$(printf '%s\n' "$clean" | tail -n "$max")
  fi
  sums=$(printf '%s\n' "$clean" | grep -E "$sumpat")
  out=$(printf '%s\n%s\n' "$errs" "$sums" | awk 'NF && !seen[$0]++' | head -n "$max")
  echo
  echo "── ❌ $name ──"
  printf '%s\n' "$out"
  case $clean in *␍*) echo "hint: ␍ = CRLF line endings in the working copy (git core.autocrlf=$(git config core.autocrlf)), not code errors" ;; esac
  if [ ${#changed[@]} -gt 0 ]; then
    hits=()
    for f in "${changed[@]}"; do
      key="$(basename "$(dirname "$f")")/$(basename "$f")"
      case $clean in *"$key"* | *"${key//\//\\}"*) hits+=("$(basename "$f")") ;; esac
    done
    if [ ${#hits[@]} -gt 0 ]; then echo "your changed files in this log: ${hits[*]}"
    else echo "none of your ${#changed[@]} changed files appear in this log"; fi
  fi
  case $name in lint*) [ -n "${fix_ok:-}" ] && echo "fix passed on your changed files, so these lint errors are in files you did not change" ;; esac
  echo "full log: $(cygpath -m "$log" 2>/dev/null || echo "$log")"
done

[ ${#failed[@]} -eq 0 ]
