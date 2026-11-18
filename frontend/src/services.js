const API=(import.meta.env.VITE_API_URL||'http://localhost:8000/api').replace(/\/$/,'');
export async function request(path,options={}){const r=await fetch(API+path,{headers:{'Content-Type':'application/json'},...options});if(!r.ok)throw new Error((await r.json()).detail||'Request failed');return r.json()}
