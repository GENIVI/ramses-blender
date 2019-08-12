#version 300 es

in vec3 a_position;
uniform highp mat4 u_ModelMatrix;
uniform highp mat4 u_ViewMatrix;
uniform highp mat4 u_ProjectionMatrix;

void main()
{
	vec3 new_pos = a_position;

	new_pos.x += 2.0f;
	new_pos.y += 2.0f;
	new_pos.z += 2.0f;

	
	gl_Position = u_ProjectionMatrix * u_ViewMatrix * u_ModelMatrix * vec4(new_pos.xyz, 1.0);
}
