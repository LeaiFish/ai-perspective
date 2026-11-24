import { copyFile, cp, mkdir, writeFile } from 'node:fs/promises';
const out=process.env.RADAR_PUBLIC_SITE_DIR || '/data/public-site';
await mkdir(out,{recursive:true});
await copyFile('.public-export/site/index.html',`${out}/index.html`);
await copyFile('.public-export/site/focus.html', `${out}/focus.html`);
await cp('.public-export/site/data/trends', `${out}/data/trends`, {recursive:true, force:false});
await cp('.public-export/site/assets',`${out}/assets`,{recursive:true});
await cp('.public-export/site/config',`${out}/config`,{recursive:true});
await writeFile(`${out}/.nojekyll`,'');
