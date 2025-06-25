var Server = (function () {
    'use strict';
    
    //Constructor
    function Server(id, address, port, ws_port, username, password)         
    {
        //public properties
        this.id = id;
        this.address = address;
        this.port = port;
        this.ws_port = ws_port;
        this.username = username;
        this.password = password;
        this.subscribptions = {};
        
        // valid conneciton types NOT_CONNECTED, CONNECTED, CONNECTING
        this.connection = { type: 'NOT_CONNECTED' };

        // ATTENTION: servers are proxied to trigger ui update when a 
        // property changes. Date proeprties do not work with proxies 
        // therefore date properties must be stored as string and for 
        // manipulation converted back and forth between Date object
        // and string
        this.lastUpdateDate = '-';
    }
    
    Server.prototype.constructor = Server;
    
    Server.prototype.connect = function(){
        this.updateConnecting();
        try
        {
            // first attempt tot disconnect
            console.log("client: ", client);
            for (const [key, value] of Object.entries(client)) 
            {
                // ATTENTION: only attempt a disconnect if the client is connected or else we crash
                if(value != null && value != undefined && key == this.key() && this.connection.type == 'CONNECTED')
                {
                    console.log(`Disconnecting from mqtt server: $${key}, client: $${value}`);
                    try
                    {
                        value.disconnect();
                    }
                    catch(e)
                    {
                        console.error("Disconnect failed");
                        console.error(e);
                    }
                    break;
                }
            }
            this.connection.type = 'CONNECTING';
            // ATTENTION: this web paho client must connect to the mqtt server's ws_port, not the regular port
            client[this.key()] = new Paho.Client(this.address, Number(this.ws_port), "clientId" + Math.random());
            client[this.key()].onConnectionLost = onConnectionLost;
            client[this.key()].onMessageArrived = onMessageArrived;
            client[this.key()].connect({ 
                timeout: 5,
                reconnect: false,
                onFailure: onFailure,
                onSuccess: onConnect, 
                invocationContext: this // pass the server as argument to the callback success function
            });
        }
        catch(e)
        {
            console.warn("Connection to " + this.key() + " failed.");
            console.error(e);
        }
    }

    Server.prototype.key = function(){ return this.address + ":" + this.ws_port;}

    Server.prototype.updateConnected = function(){
        this.connection.type = 'CONNECTED';                        
        this.lastUpdateDate = new Date().toLocaleString();
        // EXAMPLE: alternative way to update an element without
        // redrawing the entire page
        // let id  = 'server_lastUpdate_' + this.key();
        // let element = document.getElementById(id);
        // if(element != null)
        // {
        //     element.textContent = this.lastUpdateDate;
        //     compileNgShow();
        // }
    }
    
    Server.prototype.updateDisconnected = function(){
        this.connection.type = 'NOT_CONNECTED';
        this.lastUpdateDate = new Date().toLocaleString();
    }
    
    Server.prototype.updateConnecting = function(){
        this.connection.type = 'CONNECTING';
        this.lastUpdateDate = new Date().toLocaleString();
    }
                
    return Server;
})();