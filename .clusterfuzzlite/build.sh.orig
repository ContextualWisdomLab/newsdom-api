#!/bin/bash
set -euo pipefail

cd "$SRC/newsdom-api"

uv sync --frozen --extra fuzz
export PATH="$SRC/newsdom-api/.venv/bin:$PATH"

found_fuzzer=0

while IFS= read -r -d '' fuzzer; do
	found_fuzzer=1
	fuzzer_basename=$(basename -s .py "$fuzzer")
	fuzzer_package="${fuzzer_basename}.pkg"

	pyinstaller --distpath "$OUT" --onefile --name "$fuzzer_package" "$fuzzer"
	chmod -x "$OUT/$fuzzer_package"

	cat >"$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
# LLVMFuzzerTestOneInput for fuzzer detection.
this_dir=\$(dirname "\$0")
chmod +x "\$this_dir/$fuzzer_package"
	exec "\$this_dir/$fuzzer_package" "\$@"
EOF
	chmod +x "$OUT/$fuzzer_basename"
done < <(find fuzzers -type f -name '*_fuzzer.py' -print0)

if [ "$found_fuzzer" -eq 0 ]; then
	echo "No *_fuzzer.py files found under fuzzers/" >&2
	exit 1
fi
