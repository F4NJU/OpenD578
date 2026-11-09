/* File selection only. Sizes identify capture roles, never guest data. */
export const BACKUP_ROLES = Object.freeze({flash:3145728,nand:268435456,oob:8388608,ecc:131072});
export function selectBackupSet(files){
 const selected={},ignored=[];
 for(const file of files){
  const role=Object.keys(BACKUP_ROLES).find(key=>file.size===BACKUP_ROLES[key]);
  if(!role){ignored.push(file.name);continue;}
  if(selected[role])throw new Error(`Deux fichiers correspondent à ${role} : ${selected[role].name} et ${file.name}. Sélectionner une seule capture par rôle.`);
  selected[role]=file;
 }
 const missing=Object.keys(BACKUP_ROLES).filter(role=>!selected[role]);
 if(missing.length)throw new Error(`Sauvegardes manquantes : ${missing.join(', ')}. Attendu : Flash 3 Mio, NAND 256 Mio, OOB 8 Mio, ECC 128 Kio.`);
 return {args:{...selected,boot:null,app:null,appAddress:0x08006000},ignored};
}
export function backupDescription(args){
 return Object.entries(BACKUP_ROLES).map(([role,size])=>`${role.toUpperCase()} : ${args?.[role]?.name??'à sélectionner'}${args?.[role]&&args[role].size!==size?' · taille différente du jeu de référence':''}`).join('\n');
}
