// App.js
import React, {useEffect, useState} from "react";
import io from "socket.io-client";
import axios from "axios";

const NODE = process.env.REACT_APP_NODE || "http://127.0.0.1:5000";

function App(){
  const [socket, setSocket] = useState(null);
  const [peers, setPeers] = useState([]);
  const [chain, setChain] = useState([]);
  const [pending, setPending] = useState([]);
  const [myInfo, setMyInfo] = useState(null);
  const [toNode, setToNode] = useState("");
  const [toPub, setToPub] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(()=>{
    axios.get(`${NODE}/id`).then(r=> setMyInfo(r.data));
    const s = io(NODE);
    setSocket(s);
    s.on("connect", ()=> console.log("connected"));
    s.on("peers", data => setPeers(data));
    s.on("chain", data => setChain(data));
    s.on("new_tx", tx => {
      setPending(p => [tx, ...p]);
    });
    s.on("new_block", blk => {
      setChain(prev => [blk, ...prev]);
      setPending([]);
    });
    return ()=> s.disconnect();
  }, []);

  async function send(){
    if(!toNode || !toPub || !msg) return alert("fill all");
    try{
      await axios.post(`${NODE}/send`, {
        to_node: toNode,
        to_pub: toPub,
        message: msg
      });
      setMsg("");
    }catch(e){ console.error(e); alert("send failed"); }
  }

  return (<div style={{padding:20}}>
    <h2>Node UI ({NODE})</h2>
    <div>
      <strong>My public key:</strong>
      <pre style={{maxHeight:120, overflow:'auto'}}>{myInfo ? myInfo.public_key : 'loading...'}</pre>
    </div>
    <div style={{display:'flex', gap:20}}>
      <div style={{flex:1}}>
        <h3>Send One-to-One</h3>
        <input placeholder="Recipient node URL (http://127.0.0.1:5001)" value={toNode} onChange={e=>setToNode(e.target.value)} style={{width:'100%'}}/>
        <textarea placeholder="Recipient public key (base64 PEM)" value={toPub} onChange={e=>setToPub(e.target.value)} rows={6} style={{width:'100%'}}/>
        <input placeholder="Message" value={msg} onChange={e=>setMsg(e.target.value)} style={{width:'100%'}}/>
        <button onClick={send}>Send Encrypted Message (via blockchain tx)</button>
      </div>
      <div style={{flex:1}}>
        <h3>Pending Transactions</h3>
        <div style={{maxHeight:300,overflow:'auto',background:'#f7f7f7',padding:10}}>
          {pending.map((p,i)=> <div key={i} style={{borderBottom:'1px solid #ddd',padding:6}}>
            <div><strong>from:</strong> {p.from}</div>
            <div><strong>to:</strong> {p.to}</div>
            <div><strong>message (cipher):</strong> <code style={{wordBreak:'break-all'}}>{p.message}</code></div>
          </div>)}
        </div>
      </div>
    </div>

    <h3>Chain (most recent first)</h3>
    <div style={{maxHeight:300,overflow:'auto',background:'#fff',padding:10}}>
      {chain.map((b, idx)=> <div key={idx} style={{border:'1px solid #ddd',marginBottom:8,padding:8}}>
        <div><strong>index:</strong> {b.index}</div>
        <div><strong>prev_hash:</strong> {b.prev_hash}</div>
        <div><strong>hash:</strong> {b.hash}</div>
        <div><strong>txs:</strong>
          <ul>
            {b.transactions.map((t,j)=><li key={j}><small>{t.from} → {t.to} | {t.message.slice(0,24)}...</small></li>)}
          </ul>
        </div>
      </div>)}
    </div>
  </div>);
}

export default App;
