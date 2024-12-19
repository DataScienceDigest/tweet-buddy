#!/usr/bin/bash 
# Change ownership of the project directory
# sudo chown -R ubuntu:ubuntu /home/ubuntu/tweet-buddy
# sed -i 's/\[]/\["16.171.176.57"]/' /home/ubuntu/tweet-buddy/DataScienceDigest/settings.py

# python manage.py migrate 
# python manage.py makemigrations     
# python manage.py collectstatic
# sudo certbot --nginx -d datasciencedigest.in -d www.datasciencedigest.in --non-interactive --agree-tos
# sudo service gunicorn restart
# sudo service nginx restart
#!/usr/bin/bash
# Change ownership of the project directory
sudo chown -R ubuntu:ubuntu /home/ubuntu/tweet-buddy

# # Update configuration (if needed, adjust this as per your Flask app requirements)
# sed -i 's/\[]/\["16.171.176.57"]/' /home/ubuntu/tweet-buddy/config.py

# # Install dependencies (assuming a virtual environment is being used)
# cd /home/ubuntu/tweet-buddy
# source venv/bin/activate
# pip install -r requirements.txt


# Restart Gunicorn and Nginx
sudo service gunicorn restart
sudo service nginx restart
