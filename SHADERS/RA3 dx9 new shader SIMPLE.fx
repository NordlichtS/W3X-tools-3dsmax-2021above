//placeholder parameters


//the only texture
texture DiffuseTexture <string UIName = "DiffuseTexture";>; 
bool AlphaTestEnable <string UIName = "Alpha Test Enable";> = 0 ;

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

    // Alpha test: Discard pixels with alpha below a threshold
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
