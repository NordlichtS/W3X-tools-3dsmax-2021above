//placeholder parameters
int BlendMode <string UIName = "Blend Mode (0=opaque/1=alpha/2=additive)"; int UIMin = 0; int UIMax = 2;>; //still useless

texture Texture_0 <string UIName = "Texture_0";>; 

float3 ColorAmbient <string UIName = "Color Ambient"; string UIWidget = "Color";> ;
float3 ColorDiffuse <string UIName = "Color Diffuse"; string UIWidget = "Color";> ;
float3 ColorEmissive <string UIName = "Color Emissive"; string UIWidget = "Color";> ;
float3 ColorSpecular <string UIName = "Color Specular"; string UIWidget = "Color";> ;
float Shininess <string UIName = "Shininess"; string UIWidget = "Slider"; float UIStep = 0.1;> = { 1 }; //float UIMax = 100 ? really 100 ? crazy
bool AlphaTestEnable <string UIName = "Alpha Test Enable";> = { 0 };
bool DepthWriteEnable <string UIName = "Depth Write Enable";> = { 1 };
bool CullingEnable <string UIName = "Culling Enable";> = { 1 };

//sampler for the only texture
sampler2D Texture_0Sampler <string Texture = "Texture_0"; > = sampler_state
{
    Texture = <Texture_0>; 
    MinFilter = 3;
    MagFilter = 2;
    MipFilter = 2;
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
    float4 diffuseColor = tex2D(Texture_0Sampler, input.TexCoord);

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
