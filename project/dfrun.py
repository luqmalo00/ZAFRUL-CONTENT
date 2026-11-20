import sys, numpy as np, torch, wave
from safetensors.torch import load_file
from df.enhance import enhance, init_df
model, st, _ = init_df(model_base_dir='/tmp/claude-0/dfmodel/DeepFilterNet3', epoch=None, log_level='ERROR')
sd = load_file('/tmp/claude-0/dfmodel/model.safetensors')
missing, unexpected = model.load_state_dict(sd, strict=False)
print('missing', len(missing), missing[:5], 'unexpected', len(unexpected), unexpected[:5])
model.eval()
w = wave.open(sys.argv[1]); sr = w.getframerate(); assert sr == st.sr()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
lim = float(sys.argv[3]) if len(sys.argv) > 3 else None
with torch.no_grad():
    e = enhance(model, st, torch.from_numpy(a)[None], atten_lim_db=lim)
y = (np.clip(e.squeeze().numpy(), -1, 1) * 32767).astype(np.int16)
o = wave.open(sys.argv[2], 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(y.tobytes()); o.close()
print('ok', len(y) / sr)
