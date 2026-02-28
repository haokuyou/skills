#!/bin/bash
set -euo pipefail

pane_url='x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
fallback_url='x-apple.systempreferences:com.apple.preference.security'

if open "$pane_url" >/dev/null 2>&1; then
  exit 0
fi

open "$fallback_url"
