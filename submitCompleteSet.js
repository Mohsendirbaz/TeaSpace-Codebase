const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(bodyParser.text({ type: '*/*' })); // Use text parser for all content types
app.use(cors());

// Option 1: Escaped backslashes for Windows paths
const NF3_ML_DIR = path.join(__dirname);

// Function to check write permissions
const checkWritePermissions = (dir) => {
  fs.access(dir, fs.constants.W_OK, (err) => {
    if (err) {
      console.error(`No write permission for directory: ${dir}`);
    } else {
      console.log(`Write permission granted for directory: ${dir}`);
    }
  });
};

// Check permissions for the directory at startup
checkWritePermissions(NF3_ML_DIR);

app.post('/append/:version', (req, res) => {
  const version = req.params.version;
  const filePath = path.join(
    NF3_ML_DIR,
    `Original/Batch(${version})/ConfigurationPlotSpec(${version})/U_configurations(${version}).py`
  );

  console.log(`Received request to append version: ${version}`);
  console.log(`File path: ${filePath}`);

  // Ensure the directory structure exists
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
  } catch (err) {
    console.error(`Error creating directories:`, err);
    return res.status(500).send('Error creating directories');
  }

  // Get the content from the request body
  const content = req.body;
  console.log(`Content to write: ${content}`);

  // Read the existing file content
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // File doesn't exist, create it and write the content
        fs.writeFile(filePath, content, 'utf8', (writeErr) => {
          if (writeErr) {
            console.error(`Error writing to file at ${filePath}:`, writeErr);
            return res.status(500).send('Error writing to file in nf3-ml');
          }
          res.send('File created and content written successfully');
        });
      } else {
        console.error(`Error reading file at ${filePath}:`, err);
        return res.status(500).send('Error reading file');
      }
    } else {
      // Split the file into lines
      let lines = data.split('\n');
      let shouldAppend = true;

      // Iterate over each line to find the one that contains 'filteredValues'
      lines = lines.filter((line) => {
        if (line.includes('filteredValues')) {
          shouldAppend = true;
          return false; // Delete the line
        }
        return true; // Keep the line
      });

      // Reassemble the content without the filtered line
      const updatedContent = lines.join('\n');

      // Overwrite the file without the filtered line
      fs.writeFile(filePath, updatedContent, 'utf8', (writeErr) => {
        if (writeErr) {
          console.error(`Error writing to file at ${filePath}:`, writeErr);
          return res.status(500).send('Error writing to file in nf3-ml');
        }

        // Append a new line and then the content
        if (shouldAppend) {
          const appendContent = `\n${content}`;
          fs.appendFile(filePath, appendContent, 'utf8', (appendErr) => {
            if (appendErr) {
              console.error(`Error appending to file at ${filePath}:`, appendErr);
              return res.status(500).send('Error appending to file in nf3-ml');
            }
            res.send('Filtered line deleted and content appended one line below successfully');
          });
        } else {
          res.send('No filteredValues line found, content appended successfully one line below');
        }
      });
    }
  });
});

app.listen(3052, () => {
  console.log('Append server running on port 3052');
});
