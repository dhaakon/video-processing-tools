class Shaders:
    header = '''
    #ifdef GL_ES
    precision highp float;
    #endif

    /* Outputs from the vertex shader */
    varying vec4 frag_color;
    varying vec2 tex_coord0;
    varying vec2 vUv;


    /* uniform texture samplers */
    uniform sampler2D texture0;
    uniform sampler2D texture1;

    uniform vec2 resolution;
    uniform vec2 mouse;
    uniform float time;
    '''

    my_shader = header + '''
    uniform vec2 uvsize;
    uniform vec2 uvpos;
    void main(void)
    {
        vec2 q = tex_coord0 * vec2(1, -1);
        vec2 uv = 0.5 + (q-0.5);//*(0.9);// + 0.1*sin(0.2*time));

        vec3 oricol = texture2D(texture0,vec2(q.x,1.0-q.y)).xyz;
        vec3 col;

        col.r = texture2D(texture0,vec2(uv.x+0.003,-uv.y)).x;
        col.g = texture2D(texture0,vec2(uv.x+0.000,-uv.y)).y;
        col.b = texture2D(texture0,vec2(uv.x-0.003,-uv.y)).z;

        col = clamp(col*0.5+0.5*col*col*1.2,0.0,1.0);

        //col *= 0.5 + 0.5*16.0*uv.x*uv.y*(1.0-uv.x)*(1.0-uv.y);

        col *= vec3(1.0,mouse.y/1000.0,mouse.x/1000.0);

        col *= 0.9+0.1*sin(10.0*time+uv.y*1000.0);

        col *= 0.97+0.03*sin(110.0*time);

        float comp = smoothstep( 0.2, 0.9, sin(time) );
        col = mix( col, oricol, clamp(-2.0+2.0*q.x+3.0*comp,0.0,1.0) );

        gl_FragColor = vec4(col,1.0);
    }
    '''
    # pulse (Danguafer/Silexars, 2010)
    shader_pulse = header + '''
    void main(void)
    {
        vec2 halfres = resolution.xy/2.0;
        vec2 cPos = gl_FragCoord.xy;

        cPos.x -= 0.5*halfres.x*sin(time/2.0)+0.3*halfres.x*cos(time)+halfres.x;
        cPos.y -= 0.4*halfres.y*sin(time/5.0)+0.3*halfres.y*cos(time)+halfres.y;
        float cLength = length(cPos);

        vec2 uv = tex_coord0+(cPos/cLength)*sin(cLength/30.0-time*10.0)/25.0;
        vec3 col = texture2D(texture0,uv).xyz*50.0/cLength;

        gl_FragColor = vec4(col,1.0);
    }
    '''
