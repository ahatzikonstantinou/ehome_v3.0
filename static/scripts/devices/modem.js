var Door1 = (function () {
    'use strict';
    
    //Constructor
    function Modem( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
        this.listCmd = '{"cmd":"list"}';
        this.observers = [];
        this.modems = [];
        // this.modems = [{
        //     id: "2",
        //     manufacturer: "ZTE Incorporated",
        //     model: "MF195",
        //     hardware: "gsm-umts",
        //     state: "registered",
        //     power: "on",
        //     mode: "allowed: 2g, 3g; preferred: 3g",
        //     imei: "861302000722445",
        //     operator: "GR COSMOTE"
        //     }];
    }
    
    Modem.prototype = Object.create( MqttDevice.prototype );
    Modem.prototype.constructor = Modem;

    Modem.prototype.update = function( topic, message )
    {
        if( MqttDevice.prototype.update.call( this, topic, message ) )
        {
            var data = angular.fromJson( this.state );
            if( data.modem_list )
            {
                this.modems = data.modem_list
            }
            else if( data.modem )
            {
                var modem = data.modem;
                var updated = false;
                for( var i = 0 ; i < this.modems.length ; i++ )
                {
                    if( this.modems[i].id == modem.id )
                    {
                        // update individual properties instead of [this.modems[i] = modem] in order not to re-initialise showModemInfo in modem.html
                        this.modems[i].id = modem.id;
                        this.modems[i].hardware = modem.hardware;
                        this.modems[i].state = modem.state;
                        this.modems[i].power = modem.power;
                        this.modems[i].mode = modem.mode;
                        this.modems[i].imei = modem.imei;
                        this.modems[i].operator = modem.operator;
                        updated = true;
                        console.log( 'Updated modem ', modem, ' in list of modems: ', this.modems );
                        break;
                    }
                }
                if( !updated )
                {
                    this.modems.push( modem );
                    console.log( 'Added modem ', modem, ' to list of modems: ', this.modems );
                }
            }

            for( var o = 0 ; o < this.observers.length ; o++ )
            {
                // console.log( 'Modem updating observer ', this.observers[o], ', modems: ', this.modems );
                this.observers[o].updateModems( this.modems );
            }
        }
    }

    Modem.prototype.setPublisher = function( publisher )
    {
        MqttDevice.prototype.setPublisher.call( this, publisher );

        //send a message to retrieve modem list as soon as we are assigned a publisher
        var message = new Paho.Message( this.listCmd );
        message.destinationName = this.mqtt_subscribe_topic ;
        console.log( 'Modem sending message: ', message.payloadString );
        this.publisher.send( message );
    }

    Modem.prototype.enable = function( modemId )
    {
        this._enable( modemId, true );
    }

    Modem.prototype.disable = function( modemId )
    {
        this._enable( modemId, false );
    }

    Modem.prototype._enable = function( modemId, enable )
    {
        var payload = '{"cmd":"' + ( enable ? 'enable': 'disable' ) + '", "params":' + modemId + '}';
        console.log( 'Modem (', this, ') will send payload ', payload, ' to topic ', this.mqtt_subscribe_topic );
        if( this.publisher )
        {                
            var message = new Paho.Message( payload );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Modem sending message: ', message.payloadString );
            this.publisher.send( message );

            // this.state.main = value;//debugging
        }
    }

    Modem.prototype.refresh = function( modemId )
    {
        var payload = '{"cmd":"status", "params":' + modemId + '}';
        console.log( 'Modem (', this, ') will send payload ', payload, ' to topic ', this.mqtt_subscribe_topic );
        if( this.publisher )
        {                
            var message = new Paho.Message( payload );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Modem sending message: ', message.payloadString );
            this.publisher.send( message );

            // this.state.main = value;//debugging
        }            
    }

    Modem.prototype.addModemObserver = function( observer )
    {
        this.observers.push( observer );
    }

    return Modem;
})();