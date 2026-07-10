# Termux Deployment

## Install

```bash
pkg update -y
pkg install -y git python nodejs
cd ~
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
bash scripts/install_termux.sh
cp .env.example .env
nano .env
```

## Manual run

Session 1:

```bash
cd ~/new-nova
bash scripts/start_web.sh
```

Session 2:

```bash
cd ~/new-nova
bash scripts/start_bot.sh
```

## PM2 run

```bash
npm install -g pm2
cd ~/new-nova
pm2 start ecosystem.config.js
pm2 save
```

## Update

```bash
cd ~/new-nova && bash scripts/update_termux.sh
```

## Rollback

```bash
cd ~/new-nova
git log --oneline -10
git reset --hard <GOOD_COMMIT_SHA>
npm install
pip install -r requirements.txt
pm2 restart ecosystem.config.js --update-env
```
