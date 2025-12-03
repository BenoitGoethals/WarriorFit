sudo docker stop warriorfit-app
udo docker rm warriorfit-ap
sudo docker run -d --restart unless-stopped --name warriorfit-app -p 8500:8000 warriorfit-app




