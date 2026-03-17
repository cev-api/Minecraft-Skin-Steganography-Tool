import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageDraw
from Crypto.Cipher import AES
import hashlib
import requests
import base64
import json
import io
import os
import zlib

MAGIC = b"CEVAPI" # Feel free to change this :)
UI_FONT = ("Arial", 10) 

class MinecraftStegoTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Steganography Tool by CevAPI")
        self.root.geometry("500x620") 
        self.root.resizable(False, False)

        self.loaded_img = None
        self.processed_img = None
        self.display_tk_img = None 
        self.imgur_client_id = "YOUR_IMGUR_CLIENT_ID" 

        # Username/UUID input
        input_frame = tk.Frame(root)
        input_frame.pack(pady=(15, 2), padx=40, fill=tk.X)
        
        self.name_entry = tk.Entry(input_frame, font=UI_FONT, justify='center', fg='gray')
        self.name_entry.insert(0, "Username / UUID")
        self.name_entry.pack(fill=tk.X)
        
        # Placeholder events
        self.name_entry.bind("<FocusIn>", self.clear_placeholder)
        self.name_entry.bind("<FocusOut>", self.restore_placeholder)

        # Buttons
        button_row = tk.Frame(root)
        button_row.pack(pady=5)
        tk.Button(button_row, text="Fetch Skin", command=self.fetch_skin_from_mojang, 
                  bg="#4CAF50", fg="white", width=15, relief=tk.FLAT, font=UI_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(button_row, text="Browse Local PNG", command=self.load_local_file, 
                  width=15, font=UI_FONT).pack(side=tk.LEFT, padx=5)

        # Preview Panel
        self.img_panel = tk.Label(root, bg="#eeeeee", bd=1, relief=tk.SOLID)
        self.img_panel.pack(pady=5)
        self.draw_empty_preview()

        # Options
        option_frame = tk.Frame(root)
        option_frame.pack(pady=2)
        self.use_comp = tk.BooleanVar(value=True)
        self.use_enc = tk.BooleanVar(value=False)
        tk.Checkbutton(option_frame, text="Use Compression", variable=self.use_comp, font=UI_FONT).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(option_frame, text="Use Encryption", variable=self.use_enc, font=UI_FONT).pack(side=tk.LEFT, padx=10)

        # Password
        pwd_frame = tk.Frame(root)
        pwd_frame.pack(pady=2)
        tk.Label(pwd_frame, text="Password:", font=UI_FONT).pack(side=tk.LEFT)
        self.pwd_entry = tk.Entry(pwd_frame, show="*", width=25, justify='center', font=UI_FONT)
        self.pwd_entry.pack(side=tk.LEFT, padx=5)

        # Meessage Text Area
        self.text_area = scrolledtext.ScrolledText(root, width=55, height=7, font=("Consolas", 10))
        self.text_area.pack(padx=20, pady=10)

        # Action Buttons
        btn_grid = tk.Frame(root)
        btn_grid.pack(pady=(5, 10))
        tk.Button(btn_grid, text="Decode Current", command=lambda: self.process_decode(manual=True), 
                  width=18, font=UI_FONT).grid(row=0, column=0, padx=5, pady=3)
        tk.Button(btn_grid, text="Encode Message", command=self.process_encode, 
                  width=18, bg="#2196F3", fg="white", relief=tk.FLAT, font=UI_FONT).grid(row=0, column=1, padx=5, pady=3)
        tk.Button(btn_grid, text="Save Locally", command=self.save_local, 
                  width=18, font=UI_FONT).grid(row=1, column=0, padx=5, pady=3)
        tk.Button(btn_grid, text="Upload to Imgur", command=self.upload_imgur, 
                  width=18, bg="#1bb76e", fg="white", relief=tk.FLAT, font=UI_FONT).grid(row=1, column=1, padx=5, pady=3)

    # UI Helper Methods
    def clear_placeholder(self, event):
        if self.name_entry.get() == "Username / UUID":
            self.name_entry.delete(0, tk.END)
            self.name_entry.config(fg='black')

    def restore_placeholder(self, event):
        if not self.name_entry.get():
            self.name_entry.insert(0, "Username / UUID")
            self.name_entry.config(fg='gray')

    def draw_empty_preview(self):
        p = Image.new('RGBA', (256, 256), (220, 220, 220, 255))
        self.display_tk_img = ImageTk.PhotoImage(p)
        self.img_panel.config(image=self.display_tk_img)

    def update_display(self, img):
        bg = Image.new('RGBA', (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(bg)
        sz = 16
        for y in range(0, 256, sz):
            for x in range(0, 256, sz):
                if (x // sz + y // sz) % 2 == 0:
                    draw.rectangle([x, y, x + sz, y + sz], fill=(230, 230, 230, 255))
        fg = img.resize((256, 256), Image.NEAREST).convert("RGBA")
        bg.alpha_composite(fg)
        self.display_tk_img = ImageTk.PhotoImage(bg)
        self.img_panel.config(image=self.display_tk_img)

    # Core Logic
    def derive_key(self, password):
        return hashlib.sha256(password.encode()).digest()

    def calculate_full_payload_size_bits(self, raw_text):
        flags, payload = 0, raw_text
        if self.use_comp.get():
            payload = zlib.compress(payload, level=9)
            flags |= 1
        if self.use_enc.get():
            flags |= 2
            payload_len = 8 + len(payload)  # AES-CTR nonce (8) + ciphertext
        else:
            payload_len = len(payload)
        full_payload_len = len(MAGIC) + 1 + 4 + payload_len
        return full_payload_len * 8

    def chars_over_capacity(self, message_text, capacity_bits):
        if not message_text:
            return 0
        lo, hi = 0, len(message_text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            mid_bits = self.calculate_full_payload_size_bits(message_text[:mid].encode('utf-8'))
            if mid_bits <= capacity_bits:
                lo = mid
            else:
                hi = mid - 1
        return len(message_text) - lo

    def process_encode(self):
        if not self.loaded_img: return
        raw_message = self.text_area.get("1.0", tk.END).strip()
        raw_text = raw_message.encode('utf-8')
        if not raw_text: return
        flags, payload = 0, raw_text
        if self.use_comp.get():
            payload = zlib.compress(payload, level=9)
            flags |= 1
        if self.use_enc.get():
            password = self.pwd_entry.get()
            if not password:
                messagebox.showerror("Error", "Password required for encryption!")
                return
            cipher = AES.new(self.derive_key(password), AES.MODE_CTR)
            payload = cipher.nonce + cipher.encrypt(payload)
            flags |= 2
        full_payload = MAGIC + flags.to_bytes(1, 'big') + len(payload).to_bytes(4, 'big') + payload
        bits = ''.join(format(b, '08b') for b in full_payload)
        img = self.loaded_img.copy()
        px = img.load()
        w, h = img.size
        capacity_bits = w * h * 3
        if len(bits) > capacity_bits:
            chars_over = self.chars_over_capacity(raw_message, capacity_bits)
            messagebox.showerror("Capacity Exceeded", f"Message too large by {chars_over} character(s).")
            return
        idx = 0
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                c = [r, g, b]
                for i in range(3):
                    if idx < len(bits):
                        c[i] = (c[i] & ~1) | int(bits[idx])
                        idx += 1
                px[x, y] = (c[0], c[1], c[2], a)
                if idx >= len(bits): break
            if idx >= len(bits): break
        self.processed_img = img
        self.update_display(self.processed_img)
        messagebox.showinfo("Success", "Message encoded into skin.")

    def process_decode(self, manual=False):
        img = self.processed_img if self.processed_img else self.loaded_img
        if not img: return
        px, (w, h) = img.load(), img.size
        all_bits = ""
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                all_bits += f"{r&1}{g&1}{b&1}"
        all_bytes = bytes(int(all_bits[i:i+8], 2) for i in range(0, len(all_bits), 8) if i+8 <= len(all_bits))
        if all_bytes[:3] != MAGIC:
            if manual: messagebox.showinfo("Info", "No hidden data found.")
            return
        flags = all_bytes[3]
        data_len = int.from_bytes(all_bytes[4:8], byteorder='big')
        payload = all_bytes[8:8+data_len]
        if flags & 2: # Encrypted
            password = self.pwd_entry.get()
            if not password:
                messagebox.showwarning("Locked", "Encrypted data found! Enter password and Decode.")
                return
            try:
                nonce, ciphertext = payload[:8], payload[8:]
                cipher = AES.new(self.derive_key(password), AES.MODE_CTR, nonce=nonce)
                payload = cipher.decrypt(ciphertext)
            except:
                messagebox.showerror("Error", "Decryption failed.")
                return
        if flags & 1: # Compressed
            try: payload = zlib.decompress(payload)
            except: return
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, payload.decode('utf-8'))
        if not manual: messagebox.showinfo("Steganography Alert", "Hidden message extracted!")

    def fetch_skin_from_mojang(self):
        name = self.name_entry.get().strip()
        if name == "Username / UUID": return
        try:
            res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}", timeout=5)
            uuid = res.json()['id']
            res = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}", timeout=5)
            tex_b64 = res.json()['properties'][0]['value']
            tex_json = json.loads(base64.b64decode(tex_b64))
            img_res = requests.get(tex_json['textures']['SKIN']['url'], timeout=5)
            self.loaded_img = Image.open(io.BytesIO(img_res.content)).convert('RGBA')
            self.processed_img = None
            self.update_display(self.loaded_img)
            self.process_decode(manual=False)
        except: messagebox.showerror("Error", "Could not fetch skin.")

    def load_local_file(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path:
            self.loaded_img = Image.open(path).convert('RGBA')
            self.processed_img = None
            self.update_display(self.loaded_img)
            self.process_decode(manual=False)

    def save_local(self):
        img = self.processed_img if self.processed_img else self.loaded_img
        if img:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path: img.save(path)

    def upload_imgur(self):
        img = self.processed_img if self.processed_img else self.loaded_img
        if not img: return
        try:
            buf = io.BytesIO(); img.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue())
            res = requests.post("https://api.imgur.com/3/image", 
                                headers={"Authorization": f"Client-ID {self.imgur_client_id}"}, 
                                data={"image": b64, "type": "base64"}, timeout=10)
            link = res.json()['data']['link']
            self.root.clipboard_clear(); self.root.clipboard_append(link)
            messagebox.showinfo("Success", f"Link copied to clipboard:\n{link}")
        except: messagebox.showerror("Error", "Imgur upload failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftStegoTool(root)
    root.mainloop()
