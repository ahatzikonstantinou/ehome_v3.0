var Window1R = (function () {
    'use strict';
    
    //Constructor
    function Window1R( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Window1R.prototype = Object.create( MqttDevice.prototype );
    Window1R.prototype.constructor = Window1R;

    return Window1R;
})();
