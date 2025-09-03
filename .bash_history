cd /opt/telegram-bot-src
git init
qq
wq
q
exti
exit
cd /opt/telegram-bot-src
git config --global init.defaultBranch main
git init
git remote add origin https://github.com/avekutepov/suggestions_tg_bot
git pull
ssh-keygen -t ed25519 -C "botuser@cloud-001" -f ~/.ssh/id_ed25519 -N ""
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
cd /opt/telegram-bot-src
git remote set-url origin git@github.com:avekutepov/suggestions_tg_bot.git
git fetch origin
git switch -c main || git checkout -B main
git pull --rebase origin main
sudo -u botuser -H bash -l
exit
