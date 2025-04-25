import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';
import fs from 'fs';
import path from 'path';
import postcss from 'postcss';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read the input CSS file
const inputCss = fs.readFileSync('./src/index.css', 'utf8');

// Process it with PostCSS and Tailwind
postcss([
  tailwindcss('./tailwind.config.js'),
  autoprefixer
])
  .process(inputCss, { from: './src/index.css', to: './dist/tailwind.css' })
  .then(result => {
    // Create the output directory if it doesn't exist
    if (!fs.existsSync('./dist')) {
      fs.mkdirSync('./dist');
    }
    
    // Write the processed CSS to the output file
    fs.writeFileSync('./dist/tailwind.css', result.css);
    
    if (result.map) {
      fs.writeFileSync('./dist/tailwind.css.map', result.map.toString());
    }
    
    console.log('Tailwind CSS build completed successfully!');
  })
  .catch(error => {
    console.error('Error processing Tailwind CSS:', error);
    process.exit(1);
  }); 