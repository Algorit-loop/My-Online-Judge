import { build } from 'esbuild';
import { readFileSync } from 'fs';

const result = await build({
    entryPoints: ['entry.js'],
    bundle: true,
    format: 'iife',
    minify: true,
    sourcemap: false,
    target: ['es2020'],
    outfile: '../../resources/vnoj/codemirror6/codemirror-ide.min.js',
    metafile: true,
    legalComments: 'none',
});

// Print bundle analysis
const outputs = result.metafile.outputs;
for (const [file, info] of Object.entries(outputs)) {
    console.log(`${file}: ${(info.bytes / 1024).toFixed(1)} KB`);
}
