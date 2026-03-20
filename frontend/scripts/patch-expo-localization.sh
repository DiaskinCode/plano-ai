#!/bin/bash

# Patch expo-localization to support iOS 16+ calendar types
# This script fixes the missing calendar cases in LocalizationModule.swift

set -e

TARGET_FILE="node_modules/expo-localization/ios/LocalizationModule.swift"
PATCH_MARKER="iOS 16+ additional calendar types"

echo "🔧 Patching expo-localization for iOS 16+ calendar support..."

# Check if file exists
if [ ! -f "$TARGET_FILE" ]; then
  echo "❌ Target file not found: $TARGET_FILE"
  echo "   Run 'npm install' first"
  exit 1
fi

# Check if already patched
if grep -q "$PATCH_MARKER" "$TARGET_FILE"; then
  echo "✅ Already patched - no action needed"
  exit 0
fi

# Apply the patch - replace the switch statement
# We'll use sed to add the missing cases before the closing brace

# First, let's check if we need to add the cases
if grep -q "case .bangla:" "$TARGET_FILE"; then
  echo "✅ Already contains iOS 16+ calendar cases"
  exit 0
fi

# Add the missing calendar cases before the closing brace of the switch statement
# We insert them before the last } which closes the switch
perl -i -pe '
  # Find the line with "case .iso8601:" and add new cases after it
  if (/case .iso8601:/) {
    print;
    $_ = "";
    print "    // iOS 16+ additional calendar types\n";
    print "    case .bangla:\n";
    print "      return \"bangla\"\n";
    print "    case .gujarati:\n";
    print "      return \"gujarati\"\n";
    print "    case .kannada:\n";
    print "      return \"kannada\"\n";
    print "    case .malayalam:\n";
    print "      return \"malayalam\"\n";
    print "    case .marathi:\n";
    print "      return \"marathi\"\n";
    print "    case .odia:\n";
    print "      return \"odia\"\n";
    print "    case .tamil:\n";
    print "      return \"tamil\"\n";
    print "    case .telugu:\n";
    print "      return \"telugu\"\n";
    print "    case .vietnamese:\n";
    print "      return \"vietnamese\"\n";
    print "    case .vikram:\n";
    print "      return \"vikram\"\n";
    print "    case .dangi:\n";
    print "      return \"dangi\"\n";
    print "    @unknown default:\n";
    print "      return \"iso8601\"\n";
    next;
  }
  # Remove the old default case if it exists without @unknown
  if (/^    default:/) {
    $_ = "";
  }
' "$TARGET_FILE"

echo "✅ Successfully patched expo-localization for iOS 16+ calendar types"
