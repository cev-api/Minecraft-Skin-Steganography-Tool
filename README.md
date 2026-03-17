# Minecraft Skin Steganography Tool

A desktop Python app for hiding and extracting compressed and encrypted text inside Minecraft skin PNG files using LSB steganography.

Uploaded skins act as persistent, publicly accessible carrier and the embedded data remains intact until the skin is changed. Anyone with the username or UUID can retrieve the skin and extract the payload, making it a small but durable container for covert data within the limits of the image filesize.

![UI](https://i.imgur.com/EJoY9KS.png)

## What It Does

- Loads skins from local PNG files or fetches by Minecraft username/UUID (Mojang API)
- Encodes hidden text into skin pixels (LSB steganography)
- Decodes hidden text from loaded skins
- Optional payload compression (`zlib`)
- Optional payload encryption (AES-CTR with password-derived key)
- Saves modified skins locally
- Optional Imgur upload support (requires your Imgur Client ID)
- Hidden payloads begin with a magic header (`CEVAPI`) so the app can reliably detect embedded data.

## Requirements

- Python 3.9+
- Packages listed in `requirements.txt`

## How To Use

1. Load a skin with **Fetch Skin** or **Browse Local PNG**.
2. Enter your message in the text box.
3. To encrypt while encoding, enable **Use Encryption** and enter a password.
4. (Optional) Enable **Use Compression**.
5. Click **Encode Message**, then **Save Locally** or **Upload to Imgur**.
6. To decrypt/decode, load the skin, click **Decode Current**, and enter the password if prompted.

## Size Limits (Important)

- The app stores data in RGB least-significant bits, so capacity is limited by image dimensions.
- A 64x64 skin has `64 * 64 * 3 = 12,288` storable bits (about `1,536` total bytes before metadata/processing overhead).
- Embedded data includes a header and flags, plus optional compression/encryption overhead.
- The maximum text length is not fixed: it changes based on your exact text content and whether compression/encryption are enabled.
- If your message is too long, the app detects it before writing and shows exactly how many characters over the limit you are.
- Can fit this entire README 12 times in a single skin.

## Imgur Upload (Optional)

To enable uploads, replace `YOUR_IMGUR_CLIENT_ID` in `MCST.py` with your own Imgur API client ID.

## Why?

- A proof of concept for covert data storage and retrieval using a widely accessible medium.
- Demonstrates a novel approach to asynchronous, public communication via game assets.
- Also works as a fun steganography-based easter egg system.

## License

This project is licensed under the GNU General Public License v3.0. See `LICENSE`.
