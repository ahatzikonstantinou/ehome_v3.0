var Net = (function () {
    'use strict';
    
    //Constructor
    function Net( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Net.prototype = Object.create( MqttDevice.prototype );
    Net.prototype.constructor = Net;

    return Net;
})();