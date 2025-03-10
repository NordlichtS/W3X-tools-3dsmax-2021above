//input parameters, some are placeholders
float3 HCpreviewRGB <string UIName = "HCpreviewRGB ( Player Color )"; string UIWidget = "Color"; string UIWidgetParams = "noalpha";> = {1, 1, 1};
texture Texture_0 <string UIName = "Texture_0";>; 
float3 ColorAmbient <string UIName = "Color Ambient"; string UIWidget = "Color"; string UIWidgetParams = "noalpha";> = {1, 1, 1}; 
float3 ColorDiffuse <string UIName = "Color Diffuse"; string UIWidget = "Color"; string UIWidgetParams = "noalpha";> = {1, 1, 1}; 
float3 ColorEmissive <string UIName = "Color Emissive"; string UIWidget = "Color"; string UIWidgetParams = "noalpha";> = {0, 0, 0}; 
float3 ColorSpecular <string UIName = "Color Specular"; string UIWidget = "Color"; string UIWidgetParams = "noalpha";> = {1, 1, 1}; 
float Shininess <string UIName = "Shininess" ; string UIWidget = "Slider"; float UIMax = 1; float UIMin = 0; float UIStep = 0.1;> = { 1 };
bool AlphaTestEnable <string UIName = "Alpha Test Enable";> = false ;
bool DepthWriteEnable <string UIName = "Depth Write Enable";> = true ;
bool CullingEnable <string UIName = "Culling Enable";> = true ;
int BlendMode <string UIName = "Blend Mode (0=opaque/1=alpha/2=additive)"; int UIMin = 0; int UIMax = 2;> = { 0 } ;


//the useful samplers
sampler DiffuseSampler = sampler_state 
{
    Texture = <Texture_0>; 
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
    // Sample the texture
    float4 diffuseColor = tex2D(DiffuseSampler, input.TexCoord);

    // Lerp between HCpreviewRGB and DiffuseColor based on hc weight
    float3 finalColor = lerp( diffuseColor.rgb, HCpreviewRGB.rgb * diffuseColor.rgb , diffuseColor.a);
        
    // Alpha test: Discard pixels with alpha below a threshold
    if (AlphaTestEnable && diffuseColor.a < 0.5)
        discard;

    return float4(finalColor, 1.0);  // or return float4(finalColor, finalColor.a);
}


technique MainTechnique
{
    pass Pass1
    {
        vertexShader = compile vs_3_0 VS_Main();
        pixelShader = compile ps_3_0 PS_Main();
    }
}
