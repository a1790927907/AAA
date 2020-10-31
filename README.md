## Introduction
- sp_requests采用了requests模块实现
    - 数据库采用redis+mysql
    - main.py为主入口  
- sp_scrapy采用了scrapy框架实现
    - 数据库采用redis+mongodb
    - main.py为主入口
- docker-compose使用
    - 使用docker-compose -f docker-compose_requests.yml up -d --build直接运行sp_requests
    - 使用docker-compose -f docker-compose_scrapy.yml up -d --build直接运行sp_scrapy
