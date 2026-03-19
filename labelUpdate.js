const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Path configuration
const PROJECT_ROOT = path.resolve(__dirname);
const SRC_DIR = path.join(PROJECT_ROOT, 'src');
const BACKEND_DIR = path.join(PROJECT_ROOT, 'backend', 'Utility_functions');

// Helper function to create incremental backups
const createBackup = (filePath) => {
  if (!fs.existsSync(filePath)) {
    return false;
  }

  const dirName = path.dirname(filePath);
  const baseName = path.basename(filePath);
  const extension = path.extname(baseName);
  const fileName = baseName.replace(extension, '');

  let backupNumber = 1;
  let backupPath = path.join(dirName, `${fileName}_backup${backupNumber}${extension}`);

  while (fs.existsSync(backupPath)) {
    backupNumber++;
    backupPath = path.join(dirName, `${fileName}_backup${backupNumber}${extension}`);
  }

  fs.copyFileSync(filePath, backupPath);
  console.log(`Created backup at: ${backupPath}`);
  return true;
};

// Enhanced endpoint for partial updates
app.post('/api/update-form-values', (req, res) => {
  try {
    const { updates } = req.body;

    if (!updates || Object.keys(updates).length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No updates provided'
      });
    }

    const useFormValuesPath = path.join(SRC_DIR, 'useFormValues.js');
    const commonUtilsPath = path.join(BACKEND_DIR, 'common_utils.py');

    // Create backups first
    const useFormValuesBackupSuccess = createBackup(useFormValuesPath);
    const commonUtilsBackupSuccess = createBackup(commonUtilsPath);

    if (!useFormValuesBackupSuccess || !commonUtilsBackupSuccess) {
      return res.status(500).json({
        success: false,
        message: 'Failed to create backups. One or more files not found.'
      });
    }

    // 1. Process useFormValues.js
    let useFormValuesContent = fs.readFileSync(useFormValuesPath, 'utf8');

    // Update propertyMapping (only edited labels)
    const propertyMappingRegex = /const propertyMapping = \{[\s\S]*?\};/;
    const propertyMappingMatch = useFormValuesContent.match(propertyMappingRegex);

    if (!propertyMappingMatch) {
      return res.status(500).json({
        success: false,
        message: 'Could not find propertyMapping in useFormValues.js'
      });
    }

    let propertyMappingContent = propertyMappingMatch[0];
    Object.keys(updates).forEach(key => {
      const regex = new RegExp(`"${key}":\\s*"[^"]*"`);
      if (regex.test(propertyMappingContent)) {
        propertyMappingContent = propertyMappingContent.replace(
            regex,
            `"${key}": "${updates[key].label}"`
        );
      } else {
        console.warn(`Key ${key} not found in propertyMapping`);
      }
    });

    // Update defaultValues (only for edited labels)
    const defaultValuesRegex = /const defaultValues = \{[\s\S]*?\};/;
    const defaultValuesMatch = useFormValuesContent.match(defaultValuesRegex);

    if (!defaultValuesMatch) {
      return res.status(500).json({
        success: false,
        message: 'Could not find defaultValues in useFormValues.js'
      });
    }

    let defaultValuesContent = defaultValuesMatch[0];
    Object.keys(updates).forEach(key => {
      // Only update default values for fields where the label was edited
      if (updates[key].labelEdited) {
        // More robust regex that handles various formats of the default value
        // This handles numbers, strings, booleans, arrays, and both quoted and unquoted keys
        // The pattern matches the key followed by a colon, then captures everything up to the next comma or closing brace
        const regex = new RegExp(`("${key}"|${key})\\s*:\\s*([^,}]*(\\{[^}]*\\})?[^,}]*)[,}]`);
        let match = defaultValuesContent.match(regex);

        // Special handling for vAmount and rAmount keys that might be in Object.fromEntries
        if (!match) {
          // Check if this is a vAmount or rAmount key
          const vAmountMatch = key.match(/^vAmount(\d+)$/);
          const rAmountMatch = key.match(/^rAmount(\d+)$/);

          if (vAmountMatch && vAmountMatch[1] >= 40 && vAmountMatch[1] <= 59) {
            // This is a vAmount key, update only this specific key in the Object.fromEntries expression
            console.log(`Special handling for vAmount key: ${key}`);

            // Extract the specific index for this vAmount key (0-19)
            const vIndex = parseInt(vAmountMatch[1]) - 40;

            // Create a new Object.fromEntries expression that updates only the specific key
            // We'll use a conditional inside the mapping function to apply different values based on the index
            const newValue = JSON.stringify(updates[key].value);

            // Find the current Object.fromEntries expression for vAmount
            const vEntriesRegex = /\.\.\.Object\.fromEntries\(\s*Array\.from\(\{\s*length:\s*20\s*\},\s*\(_,\s*i\)\s*=>\s*\[`vAmount\$\{40\s*\+\s*i\}`,([^\]]*)\]\s*\)\s*\),/;
            const vEntriesMatch = defaultValuesContent.match(vEntriesRegex);

            if (vEntriesMatch) {
              // Get the current value used for all vAmount keys
              const currentValue = vEntriesMatch[1].trim();

              // Replace with a new expression that uses a conditional to apply different values
              defaultValuesContent = defaultValuesContent.replace(
                vEntriesRegex,
                `...Object.fromEntries(Array.from({ length: 20 }, (_, i) => [\`vAmount\${40 + i}\`, i === ${vIndex} ? ${newValue} : ${currentValue}])),`
              );

              console.log(`Updated vAmount${vAmountMatch[1]} to ${newValue} while preserving other values`);
              return; // Skip the rest of the loop for this key
            }
          }

          if (rAmountMatch && rAmountMatch[1] >= 60 && rAmountMatch[1] <= 79) {
            // This is an rAmount key, update only this specific key in the Object.fromEntries expression
            console.log(`Special handling for rAmount key: ${key}`);

            // Extract the specific index for this rAmount key (0-19)
            const rIndex = parseInt(rAmountMatch[1]) - 60;

            // Create a new Object.fromEntries expression that updates only the specific key
            // We'll use a conditional inside the mapping function to apply different values based on the index
            const newValue = JSON.stringify(updates[key].value);

            // Find the current Object.fromEntries expression for rAmount
            const rEntriesRegex = /\.\.\.Object\.fromEntries\(\s*Array\.from\(\{\s*length:\s*20\s*\},\s*\(_,\s*i\)\s*=>\s*\[`rAmount\$\{60\s*\+\s*i\}`,([^\]]*)\]\s*\)\s*\)/;
            const rEntriesMatch = defaultValuesContent.match(rEntriesRegex);

            if (rEntriesMatch) {
              // Get the current value used for all rAmount keys
              const currentValue = rEntriesMatch[1].trim();

              // Replace with a new expression that uses a conditional to apply different values
              defaultValuesContent = defaultValuesContent.replace(
                rEntriesRegex,
                `...Object.fromEntries(Array.from({ length: 20 }, (_, i) => [\`rAmount\${60 + i}\`, i === ${rIndex} ? ${newValue} : ${currentValue}]))`
              );

              console.log(`Updated rAmount${rAmountMatch[1]} to ${newValue} while preserving other values`);
              return; // Skip the rest of the loop for this key
            }
          }
        }

        if (match) {
          // Extract the matched text and determine the key format and separator
          const matchedText = match[0];
          const isLastItem = matchedText.endsWith('}');
          const separator = isLastItem ? '}' : ',';

          // Determine if the key in the original text is quoted or not
          const keyFormat = matchedText.trim().startsWith(`"${key}"`) ? `"${key}"` : key;

          // Create replacement with the same key format and ending character
          // Use JSON.stringify to properly format the value (handles strings, numbers, booleans, etc.)
          const replacement = `${keyFormat}: ${JSON.stringify(updates[key].value)}${separator}`;

          console.log(`Replacing: "${matchedText}" with "${replacement}"`); // Debug log

          // Replace the matched text with our replacement
          defaultValuesContent = defaultValuesContent.replace(matchedText, replacement);

          console.log(`Updated default value for ${key} to ${JSON.stringify(updates[key].value)}`);
        } else {
          console.warn(`Key ${key} not found in defaultValues`);
        }
      }
    });

    // Apply both updates to the file content
    let updatedContent = useFormValuesContent
        .replace(propertyMappingRegex, propertyMappingContent)
        .replace(defaultValuesRegex, defaultValuesContent);

    fs.writeFileSync(useFormValuesPath, updatedContent, 'utf8');

    // 2. Process common_utils.py (only property_mapping)
    let commonUtilsContent = fs.readFileSync(commonUtilsPath, 'utf8');
    const pythonPropertyMappingRegex = /property_mapping = \{[\s\S]*?\}/;
    const pythonPropertyMappingMatch = commonUtilsContent.match(pythonPropertyMappingRegex);

    if (!pythonPropertyMappingMatch) {
      return res.status(500).json({
        success: false,
        message: 'Could not find property_mapping in common_utils.py'
      });
    }

    let pythonPropertyMappingContent = pythonPropertyMappingMatch[0];
    Object.keys(updates).forEach(key => {
      const regex = new RegExp(`"${key}":\\s*"[^"]*"`);
      if (regex.test(pythonPropertyMappingContent)) {
        pythonPropertyMappingContent = pythonPropertyMappingContent.replace(
            regex,
            `"${key}": "${updates[key].label}"`
        );
      }
    });

    const updatedCommonUtilsContent = commonUtilsContent.replace(
        pythonPropertyMappingRegex,
        pythonPropertyMappingContent
    );

    fs.writeFileSync(commonUtilsPath, updatedCommonUtilsContent, 'utf8');

    res.json({
      success: true,
      message: `Successfully updated ${Object.keys(updates).length} items`,
      updatedItems: Object.keys(updates),
      backups: {
        useFormValues: path.basename(useFormValuesPath) + '_backup',
        commonUtils: path.basename(commonUtilsPath) + '_backup'
      }
    });

  } catch (error) {
    console.error('Error updating form values:', error);
    res.status(500).json({
      success: false,
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'Label Update Service'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    success: false,
    message: 'Internal server error',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Get port from command line arguments or use default
const PORT = process.argv.includes('--port') 
  ? parseInt(process.argv[process.argv.indexOf('--port') + 1], 10) 
  : 3060;

app.listen(PORT, () => {
  console.log(`Label Update server running on port ${PORT}`);
  console.log(`Project root: ${PROJECT_ROOT}`);
  console.log(`Source directory: ${SRC_DIR}`);
  console.log(`Backend directory: ${BACKEND_DIR}`);
});

module.exports = app;
