var MotionCamera = (function () {
    'use strict';
    
    //Constructor
    function MotionCamera( mqtt_publish_topic, mqtt_subscribe_topic, cameraId, videostream, state, detection )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );

        //public properties
        this.cameraId = cameraId
        this.videostream = videostream; 
        this.detection = detection;            
        this.lastDetection = Date.now();
        this.picture = null;
    }

    MotionCamera.prototype = Object.create( MqttDevice.prototype );
    MotionCamera.prototype.constructor = MotionCamera;

    MotionCamera.prototype._cmd = function( value )
    { 
        if( this.publisher )
        { 
            var m = new Paho.Message( '{"cmd":"' + value +'", "camera":"' + this.cameraId + '"}' ); 
            m.destinationName = this.mqtt_publish_topic;
            // console.log( 'sending msg: ', m );
            this.publisher.send( m ); 
        } 
    }

    MotionCamera.prototype.startDetection = function(){ this._cmd( 'startDetection' ); }
    MotionCamera.prototype.pauseDetection = function(){ this._cmd( 'pauseDetection' ); }
    MotionCamera.prototype.getState = function(){ this._cmd( 'getState' ); }

    MotionCamera.prototype.update = function( topic, message )
    {
        if( topic == this.mqtt_subscribe_topic )
        {
            var data = angular.fromJson( message );
            // console.log( 'motion-data:',  data );
            if( data.camera == this.cameraId )
            {
                // console.log( 'MotionCamera[' + this.mqtt_subscribe_topic +']: this message is for me.' );
                if( data.state )
                {                        
                    this.state = data.state;
                    this.lastUpdate = Date.now();
                }
                else if( data.detection )
                {
                    this.detection = data.detection;
                    this.lastDetection = Date.now();
                }
                else if( data.picture )
                {
                    this.picture = data.picture;
                    // console.log( 'received picture: ', data.picture );
                }
            }
        }
    }

    return MotionCamera;
})();