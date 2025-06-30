FROM node:18-alpine

WORKDIR /app

# Kopiera package files
COPY package*.json ./

# Installera dependencies
RUN npm install

# Kopiera source code
COPY . .

# Exponera port
EXPOSE 3000

# Starta development server
CMD ["npm", "start"]