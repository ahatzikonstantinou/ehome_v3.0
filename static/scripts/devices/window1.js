var Window1 = (function () {
    'use strict';
    
    //Constructor
    function Window1( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Window1.prototype = Object.create( MqttDevice.prototype );
    Window1.prototype.constructor = Window1;

    return Window1;
})();