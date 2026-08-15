# Text Processing — grep, find, awk, sed, pipes

> Log locations: **[systemd.md](systemd.md)** · Filesystem layout: **[filesystem.md](filesystem.md)**

---

## 1. Streams, redirection & pipes

Every process gets three descriptors: **stdin (0)**, **stdout (1)**, **stderr (2)**.

```bash
cmd > out.txt              # stdout → file (TRUNCATES)
cmd >> out.txt             # append
cmd 2> err.txt             # stderr only
cmd > all.txt 2>&1         # ⭐ both → one file  (ORDER MATTERS)
cmd &> all.txt             # bash shorthand for the same
cmd 2>/dev/null            # ⭐ discard errors — e.g. find's "Permission denied" noise
cmd < input.txt            # stdin from file
cmd1 | cmd2                # stdout of cmd1 → stdin of cmd2
cmd | tee file             # ⭐ show on screen AND save
cmd | tee -a file          # append
```

⚠️ **`2>&1` must come *after* the redirect.** `cmd 2>&1 > f` sends stderr to the *terminal*
(it copies stdout's destination at that moment, which is still the terminal) and only stdout
to the file. `cmd > f 2>&1` is what you want.

⚠️ **`cmd > file` truncates before the command runs**, so `grep x file > file` empties it.
Use a temp file or `sponge` (moreutils).

**Pipes only carry stdout** — to filter errors: `cmd 2>&1 | grep -i error`.

```bash
set -o pipefail            # ⭐ in scripts: a pipeline fails if ANY stage fails,
                           #    not just the last one
```

---

## 2. grep — search content ⭐

```bash
grep "error" app.log
grep -i "error" app.log          # case-insensitive
grep -r "TODO" src/              # ⭐ recursive
grep -rn "def process" src/      # + line numbers
grep -v "healthcheck" app.log    # ⭐ INVERT — exclude noise
grep -c "error" app.log          # count matching LINES (not occurrences)
grep -l "api_key" -r .           # ⭐ just the filenames
grep -w "id" file                # whole word — not "uuid", "idle"
grep -A3 -B3 "Traceback" app.log # ⭐ 3 lines After / Before
grep -C5 "error" app.log         # 5 lines of Context both ways
grep -o "[0-9]\+\.[0-9]\+" file  # print only the MATCH, not the line
grep -E "warn|error|fatal" log   # ⭐ extended regex (= egrep)
grep -P "\d{3}-\d{4}" file       # Perl regex: \d \w \s shorthand
grep -F "1.2.3.4" file           # ⭐ Fixed string — no regex, faster & safe with dots
```

⭐ **`rg` (ripgrep)** if available: recursive by default, respects `.gitignore`, dramatically
faster on repos. `rg "def process" -t py`

**Regex quick reference:**

```
^start   $end     .any     *0+      +1+      ?0-1     [abc]     [^abc]
\.  \/  \$        literal escapes
\b  word boundary       (a|b)  alternation      {2,5}  repetition
```

⚠️ Basic grep needs `\+`, `\|`, `\{`; **`-E` makes them plain** `+ | {`. Use `-E` by default.

---

## 3. find — search by metadata ⭐

```bash
find . -name "*.log"                  # glob, case-sensitive
find . -iname "*.LOG"                 # case-insensitive
find . -type f / -type d / -type l    # files / dirs / symlinks
find . -type f -size +100M            # ⭐ big files
find /var/log -mtime +30              # modified more than 30 days ago
find . -mmin -10                      # ⭐ changed in the last 10 minutes — "what just broke?"
find . -user alice -perm -4000        # setuid audit
find . -empty
find . -maxdepth 2                    # ⭐ limit recursion (put it FIRST)
```

**Acting on results:**

```bash
find /var/log -name "*.log" -mtime +30 -delete
find . -name "*.tmp" -exec rm {} \;        # one process PER file — slow
find . -name "*.tmp" -exec rm {} +         # ⭐ batches args — much faster
find . -name "*.py" -print0 | xargs -0 grep -l "TODO"   # ⭐ NUL-safe
```

⭐⭐ **`-print0` + `xargs -0` is not optional.** Any filename containing a space breaks the
naive pipeline (`My File.txt` → two arguments). `find -exec ... +` is the other safe form.

⭐ **Always dry-run destructive finds** — swap `-delete` for `-print` first. `find` deletions
are not recoverable.

⚠️ **Order matters:** `find . -name "*.log" -maxdepth 2` warns and misbehaves;
`find . -maxdepth 2 -name "*.log"` is correct — options before tests.

```bash
find . -type d -name node_modules -prune -o -name "*.js" -print   # ⭐ skip a subtree
find . -name "*.log" 2>/dev/null                                  # silence permission noise
```

**find vs locate vs which:** `find` walks the tree live (accurate, slow) · `locate` queries a
prebuilt index (instant, possibly stale — `sudo updatedb`) · `which`/`type -a` search `$PATH`
for a command.

---

## 4. awk — column & field processing ⭐

awk splits each line into fields (`$1`, `$2`, … `$NF`) on whitespace by default and runs
`pattern { action }` on every line.

```bash
awk '{print $1}' access.log                    # first field
awk '{print $NF}' file                         # ⭐ LAST field
awk -F: '{print $1, $7}' /etc/passwd           # ⭐ -F sets the delimiter
awk '$3 > 100 {print $1, $3}' data.txt         # filter numerically then print
awk 'NR==5' file                               # line 5  (NR = record number)
awk 'NR>1' file                                # ⭐ skip a CSV header
awk 'END {print NR}' file                      # line count
awk '{sum += $3} END {print sum}' data.txt     # ⭐ SUM a column
awk '{sum+=$1} END {print sum/NR}' file        # average
awk '!seen[$0]++' file                         # ⭐ dedupe, ORDER PRESERVED (unlike sort -u)
awk '{print $9}' access.log | sort | uniq -c | sort -rn | head   # ⭐ top status codes
awk -F, '{printf "%-20s %8.2f\n", $1, $3}' data.csv              # formatted columns
```

**Built-ins:** `NR` current line number · `NF` field count · `$0` whole line · `FS`/`OFS`
input/output separators.

⭐ **awk's advantage over `cut`:** it handles *runs* of whitespace as one separator, so
`ps aux | awk '{print $2}'` works while `cut -d' ' -f2` fails on aligned output.

---

## 5. sed — stream editing

```bash
sed 's/old/new/' file             # first occurrence PER LINE
sed 's/old/new/g' file            # ⭐ all occurrences
sed 's/old/new/gi' file           # + case-insensitive
sed -i 's/old/new/g' file         # ⚠️ EDIT IN PLACE — no undo
sed -i.bak 's/old/new/g' file     # ⭐ in place, keeping file.bak
sed -n '10,20p' file              # ⭐ print lines 10–20 (-n suppresses default output)
sed '/^#/d' config                # delete comment lines
sed '/^$/d' file                  # delete blank lines
sed -n '/ERROR/,/END/p' app.log   # ⭐ a RANGE between two patterns
sed 's|/old/path|/new/path|g' f   # ⭐ any delimiter — avoids escaping slashes
```

⭐ **Always run without `-i` first.** `sed -i` on the wrong regex silently corrupts every
matching line across every file you passed it.

```bash
grep -rl "old_api" src/ | xargs sed -i.bak 's/old_api/new_api/g'   # project-wide rename
```

---

## 6. cut, sort, uniq, tr

```bash
cut -d: -f1,7 /etc/passwd      # by delimiter — ⚠️ only single-char, no whitespace runs
cut -c1-10 file                # by character position

sort file
sort -n / -rn                  # numeric / reverse numeric
sort -k3 -n file               # ⭐ by column 3
sort -t, -k2 -n data.csv       # custom delimiter
sort -u file                   # unique (sorted)
sort -h                        # ⭐ human sizes: 1K < 1M < 1G

uniq file                      # ⚠️ only collapses ADJACENT duplicates — SORT FIRST
sort file | uniq -c            # ⭐ count occurrences
sort file | uniq -d            # only duplicates
sort file | uniq -u            # only uniques

tr 'a-z' 'A-Z' < file          # translate
tr -d '\r' < win.txt > unix.txt   # ⭐ strip CRLF
tr -s ' '                      # squeeze repeated spaces
```

⚠️ **`uniq` without `sort` is the most common pipeline bug** — it only removes *consecutive*
duplicates. Use `sort | uniq -c`, or `awk '!seen[$0]++'` when order must be preserved.

---

## 7. Real pipelines ⭐

```bash
# Top 10 IPs hitting the server
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# HTTP status code distribution
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# Slowest endpoints (response time in the last field)
awk '{print $NF, $7}' access.log | sort -rn | head -20

# Errors in the last hour, grouped by message
journalctl --since "1 hour ago" -p err | awk '{$1=$2=$3=""; print}' | sort | uniq -c | sort -rn

# Largest directories under /var
du -h --max-depth=1 /var 2>/dev/null | sort -rh | head

# Every process by memory, top 10
ps aux --sort=-%mem | head -11 | awk '{print $2, $4, $11}'

# Find TODOs added by one author
grep -rn "TODO" src/ | while read -r l; do
  f="${l%%:*}"; n="$(echo "$l" | cut -d: -f2)"
  echo "$(git blame -L "$n,$n" --porcelain "$f" | head -1) $l"
done

# Follow a log, only errors, timestamped
tail -F app.log | grep --line-buffered -i error | ts
```

⭐ **`--line-buffered` matters when grepping a `tail -F`** — otherwise grep buffers 4 KB and
your "live" view stalls until the buffer fills.

---

## 8. Log-file specifics

```bash
tail -F /var/log/app.log            # ⭐ -F survives rotation; -f does not
zgrep "error" /var/log/app.log.1.gz # ⭐ search compressed logs without extracting
zcat file.gz | less
less +F file                        # follow mode inside less; Ctrl-C to scroll back
multitail a.log b.log
```

**Rotation** — `/etc/logrotate.d/myapp`:

```
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate        # ⭐ when the app can't reopen its log on signal
}
```

```bash
sudo logrotate -d /etc/logrotate.d/myapp    # ⭐ debug/dry-run
```

⚠️ **Without rotation, a log fills the disk and takes the service down.** And an app that
keeps writing to the *rotated* (deleted) file still holds the space — see `filesystem.md §4`;
`copytruncate` or a `postrotate` reload signal fixes it.

---

## 9. Interview points

- **`>` vs `>>`?** Truncate vs append.
- **What does `2>&1` do, and why does order matter?** Redirects stderr to wherever stdout
  currently points — so it must come *after* `> file`.
- **`grep -v` use case?** Excluding noise (health checks, known warnings) from a log scan.
- **Why is `uniq` not removing my duplicates?** It only collapses adjacent lines — `sort`
  first, or use `awk '!seen[$0]++'` to keep order.
- **`find -exec {} \;` vs `{} +`?** One process per file vs batched arguments — `+` is far
  faster.
- **Why `-print0 | xargs -0`?** Filenames with spaces or newlines otherwise split into
  multiple arguments.
- **awk vs cut?** awk handles whitespace runs, arithmetic, and conditions; `cut` is
  single-delimiter and positional only.
- **How do you replace a string across a project?**
  `grep -rl old . | xargs sed -i.bak 's/old/new/g'` — after verifying without `-i`.
- **`tail -f` vs `tail -F`?** `-F` reopens the file by name, so it survives log rotation.
- **What does `set -o pipefail` do?** Makes a pipeline return failure if *any* stage fails,
  not just the last — essential in scripts.
