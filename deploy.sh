sudo docker stop warriorfit-app
sudo docker rm warriorfit-ap
sudo docker build -t warriorfit-app .
sudo docker run -d --restart unless-stopped --name warriorfit-app -p 8500:8000 warriorfit-app