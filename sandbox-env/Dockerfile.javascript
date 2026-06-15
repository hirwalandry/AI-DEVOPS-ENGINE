FROM node:20-alpine
RUN npm install -g jest
WORKDIR /workspace
