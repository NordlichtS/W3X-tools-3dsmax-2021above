//placeholder parameters
texture DiffuseTexture <string UIName = "DiffuseTexture";>; 
texture NormalMap <string UIName = "NormalMap(NRM)";>; 
texture SpecMap <string UIName = "SpecMap(SPM)";>; 
float3 AmbientColor <string UIName = "Ambient Color"; string UIWidget = "Color";> = { 0.4, 0.4, 0.4 };
float4 DiffuseColor <string UIName = "Diffuse Color (RGBA)"; string UIWidget = "Color";> = { 1, 1, 1, 1 };
float3 SpecularColor <string UIName = "Specular Color"; string UIWidget = "Color";> = { 0.8, 0.8, 0.8 };
float SpecularExponent <string UIName = "Specular Exponent"; string UIWidget = "Slider"; float UIMax = 200; float UIMin = 0; float UIStep = 1;> = { 50 };
float EnvMult <string UIName = "EnvMult(Reflection)"; string UIWidget = "Slider"; float UIMax = 1; float UIMin = 0; float UIStep = 0.1;> = { 1 };
float BumpScale <string UIName = "Bump Scale (Height? NRM vector XY scale?)"; string UIWidget = "Slider"; float UIMin = 0; float UIMax = 12; float UIStep = 0.1;> = { 1 };
bool AlphaTestEnable <string UIName = "Alpha Test Enable";> ; 

sampler DiffuseSampler = sampler_state 
{
    Texture = <DiffuseTexture>; 
    MinFilter = 3;
    MagFilter = 2;
    MipFilter = 2;
    MaxAnisotropy = 8;
    AddressU = 1;
    AddressV = 1;
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

    if (AlphaTestEnable && diffuseColor.a < 0.5) discard;

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
