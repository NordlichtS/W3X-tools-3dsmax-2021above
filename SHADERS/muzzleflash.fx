//this shader is mostly for VFX and helicopter rotor, it can spin UV 
float3 ColorEmissive <string UIName = "Color Emissive"; string UIWidget = "Color";> = { 1, 1, 1 };
bool MultiTextureEnable <string UIName = "Multi Texture Enable";>;
texture Texture_0 <string UIName = "Texture_0";>; 
float TexCoordTransformAngle_0 <string UIName = "Angle_0 (Radian Delta Rate per Frame)"; string UIWidget = "Slider"; float UIMin = -100; float UIMax = 100;> = {0.25};
float TexCoordTransformU_0 <string UIName = "VertexID 0 Rotation Center U"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };
float TexCoordTransformV_0 <string UIName = "VertexID 0 Rotation Center V"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };
float TexCoordTransformU_1 <string UIName = "VertexID 1 Rotation Center U"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };
float TexCoordTransformV_1 <string UIName = "VertexID 1 Rotation Center V"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };
float TexCoordTransformU_2 <string UIName = "VertexID 2 Rotation Center U"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };
float TexCoordTransformV_2 <string UIName = "VertexID 2 Rotation Center V"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 1;> = { 0.5 };


sampler2D Texture_0Sampler = sampler_state
{
    Texture = <Texture_0>; 
    MinFilter = 3;
    MagFilter = 2;
    MipFilter = 2;
};

// Default transformations
float4x4 WorldViewProjection : WorldViewProjection;

// Vertex shader
struct VS_INPUT
{
    float4 Position : POSITION;
    float3 Normal   : NORMAL;
    float2 TexCoord : TEXCOORD0;
};

struct VS_OUTPUT
{
    float4 Position : POSITION;
    float2 TexCoord : TEXCOORD0;
};

VS_OUTPUT VS_Main(VS_INPUT input)
{
    VS_OUTPUT output;

    output.Position = mul(input.Position, WorldViewProjection);
    output.TexCoord = input.TexCoord;

    return output;
}

// Pixel shader
struct PS_INPUT
{
    float2 TexCoord : TEXCOORD0;
};

float4 PS_Main(PS_INPUT input) : COLOR
{
    // Sample the diffuse texture
    float4 diffuseColor = tex2D(DiffuseSampler, input.TexCoord);

    // Alpha blend: Combine the source color with the destination color
    return diffuseColor;
}

technique MainTechnique
{
    pass Pass1
    {
        vertexShader = compile vs_3_0 VS_Main();
        pixelShader = compile ps_3_0 PS_Main();
    }
}
