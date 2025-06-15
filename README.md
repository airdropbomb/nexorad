# 🌐 NEXORAD AUTO REFFERAL 

A lightweight automation script for joining the [Nexorad](https://waitlist.nexorad.io/?inviterCode=DPT78NXE) Web3 waitlist using rotating proxies and an invite code.

[![GitHub](https://img.shields.io/github/license/itsmesatyavir/nexorad?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/itsmesatyavir/nexorad?style=flat-square)](https://github.com/itsmesatyavir/nexorad/stargazers)

---

## 🚀 Features

- 🔁 Automates Nexorad referral submissions.
- 🔐 Uses `.env` for secure configuration.
- 🌍 Supports rotating proxies for anonymity.
- 📦 Lightweight and easy to run.

---

## 🔧 Requirements

- Python 3.7+
- `requests`
- `python-dotenv`

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/itsmesatyavir/nexorad.git
   cd nexorad
   ```

2. **Add Your Environment Variables**

   Create a `.env` file in the root directory with this content:

   ```env
   INVITER_CODE=DPT78NXE
   ```

3. **Add Proxies**

   Add one proxy per line in `proxy.txt`:

   ```
   192.168.0.1:8080
   192.168.0.2:9090:username:password
   ```

---

## ▶️ Run the Script

```bash
python main.py
```

Each execution will submit a new referral using a proxy.

---

## 📁 Project Structure

```
nexorad/
├── main.py          # Core automation script
├── .env             # Stores inviter code securely
├── proxy.txt        # List of proxies
├── LICENSE
└── README.md
```

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).

---

## 🌐 Author

Made with ❤️ by [itsmesatyavir](https://github.com/itsmesatyavir)

---

## 🌟 Star this repo

If you found this useful, consider giving it a ⭐️ to support the project!
