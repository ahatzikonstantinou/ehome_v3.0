var TemperatureHumidity = (function () {
    'use strict';
    
    //Constructor
    function TemperatureHumidity( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    TemperatureHumidity.prototype = Object.create( MqttDevice.prototype );
    TemperatureHumidity.prototype.constructor = TemperatureHumidity;

    return TemperatureHumidity;
})();