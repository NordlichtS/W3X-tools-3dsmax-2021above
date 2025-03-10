//input parameters, some are placeholders
float3 HCpreviewRGB <string UIName = "HCpreviewRGB(PlayerColor)";> = {1, 1, 1};  // Default to white
texture DiffuseTexture <string UIName = "DiffuseTexture";>; 
texture NormalMap <string UIName = "NormalMap(NRM)";>; 
texture SpecMap <string UIName = "SpecMap(SPM)";>; 
texture DamagedTexture <string UIName = "Damaged Texture";>; 
float EnvMult <string UIName = "EnvMult(Reflection)"; string UIWidget = "Slider"; float UIMax = 1; float UIMin = 0; float UIStep = 0.1;> = { 1 };
bool AlphaTestEnable <string UIName = "AlphaTestEnable(holes)";>;

//the useful samplers
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

sampler SpecSampler = sampler_state 
{
    Texture = <SpecMap>; 
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
    float4 SPMcolor = tex2D(SpecSampler, input.TexCoord);

    // Lerp between HCpreviewRGB and DiffuseColor based on hcweight
    float3 finalColor = lerp( diffuseColor.rgb, HCpreviewRGB.rgb * diffuseColor.rgb , SPMcolor.b);

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
