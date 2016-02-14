#!/bin/bash

main() {
  set -e -u -o pipefail
  if test $# -eq 0; then
    debug "Usage: $(basename $0) VIDEO [EXTRA_OPTIONS_FOR_FFMPEG]"
    exit 1
  fi
  VIDEO=$1
  echo $VIDEO
  youtube-upload --email=media@sector-alpha.net --title="$VIDEO" --description="http://sector-alpha.net $VIDEO" --category=Games $VIDEO --unlisted
}
  
test "$NOEXEC" = 1 || main "$@"

