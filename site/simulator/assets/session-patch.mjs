/* Host-side persistence. Source hashes are not read by the guest firmware. */
const roles=['flash','boot','app','nand','oob','ecc'];
export async function bindPatchSources(patch,files,hash){
 if(!files.nand)throw new Error('Charger la capture NAND avant d’exporter un correctif.');
 const baseImages={};
 for(const role of roles)baseImages[role]=files[role]?{name:files[role].name,size:files[role].size,sha256:await hash(role)}:null;
 return {...patch,baseImages};
}
export async function validatePatchSources(patch,files,hash){
 const images=patch?.baseImages;
 if(!images||typeof images!=='object')throw new Error('Ce correctif ancien ne contient pas les empreintes des sauvegardes. Le conserver pour le banc qui l’a créé ; la reprise guidée exige un export 0.15 ou ultérieur.');
 for(const role of roles){
  const expected=images[role],file=files[role];
  if(!Object.hasOwn(images,role)||Boolean(expected)!==Boolean(file))throw new Error(`${role} : jeu de sauvegardes différent du correctif.`);
  if(!expected)continue;
  if(expected.size!==file.size||typeof expected.sha256!=='string'||!/^[0-9a-f]{64}$/.test(expected.sha256))throw new Error(`${role} : taille ou empreinte source invalide.`);
 }
 for(const role of roles)if(files[role]&&await hash(role)!==images[role].sha256)throw new Error(`${role} : SHA-256 différent. Aucune page du correctif n’a été appliquée.`);
}
