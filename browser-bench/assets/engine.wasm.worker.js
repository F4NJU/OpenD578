/* Classic worker only to load Emscripten UMD and its WASM locally. */
self.__wasmFactory = async () => {
  if (typeof self.MUnicorn !== 'function') {
    try { importScripts('../vendor/unicorn_arm.js'); }
    catch(error){throw new Error('Unicorn ARM introuvable: lancer tools/vendor_unicorn_arm.sh avant de publier. '+error.message);}
  }
  if(typeof self.MUnicorn!=='function')throw new Error('Le paquet Unicorn.js ne fournit pas MUnicorn');
  if(!self.__wasmInstance){
    const wasmUrl = new URL('../vendor/unicorn_arm.wasm', self.location.href).href;
    self.__wasmInstance=await self.MUnicorn({locateFile:(filename)=>filename.endsWith('.wasm')?wasmUrl:filename});
  }
  return self.__wasmInstance;
};
import('./engine.wasm.worker.mjs?build=web0151r5').then(()=>{
  if(typeof WebAssembly!=='object'||typeof FileReaderSync!=='function')throw new Error('Ce navigateur ne fournit pas WebAssembly et FileReaderSync dans le Worker. Utiliser un navigateur de bureau récent.');
  self.postMessage({type:'ready',build:'web0151r5'});
}).catch(error=>self.postMessage({type:'startup-error',error:error.message}));
