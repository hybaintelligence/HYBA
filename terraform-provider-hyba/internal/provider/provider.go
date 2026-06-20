package provider

import (
	"context"
	"os"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/path"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"hyba-ai/terraform-provider-hyba/internal/client"
)

var (
	_ provider.Provider = &HybaProvider{}
)

func New(version string) func() provider.Provider {
	return func() provider.Provider {
		return &HybaProvider{
			version: version,
		}
	}
}

type HybaProvider struct {
	version string
}

type HybaProviderModel struct {
	Endpoint types.String `tfsdk:"endpoint"`
	ApiKey   types.String `tfsdk:"api_key"`
}

func (p *HybaProvider) Metadata(ctx context.Context, req provider.MetadataRequest, resp *provider.MetadataResponse) {
	resp.TypeName = "hyba"
	resp.Version = p.version
}

func (p *HybaProvider) Schema(ctx context.Context, req provider.SchemaRequest, resp *provider.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"endpoint": schema.StringAttribute{
				MarkdownDescription: "URI for HYBA API. May also be provided via HYBA_ENDPOINT environment variable.",
				Optional:            true,
			},
			"api_key": schema.StringAttribute{
				MarkdownDescription: "API Key for HYBA API. May also be provided via HYBA_API_KEY environment variable.",
				Optional:            true,
				Sensitive:           true,
			},
		},
	}
}

func (p *HybaProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
	var config HybaProviderModel

	resp.Diagnostics.Append(req.Config.Get(ctx, &config)...)

	if resp.Diagnostics.HasError() {
		return
	}

	endpoint := os.Getenv("HYBA_ENDPOINT")
	apiKey := os.Getenv("HYBA_API_KEY")

	if !config.Endpoint.IsNull() {
		endpoint = config.Endpoint.ValueString()
	}

	if !config.ApiKey.IsNull() {
		apiKey = config.ApiKey.ValueString()
	}

	if endpoint == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("endpoint"),
			"Missing HYBA Endpoint",
			"The provider cannot create the HYBA API client as there is a missing or empty value for the HYBA endpoint. "+
				"Set the endpoint value in the configuration or use the HYBA_ENDPOINT environment variable.",
		)
	}

	if apiKey == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("api_key"),
			"Missing HYBA API Key",
			"The provider cannot create the HYBA API client as there is a missing or empty value for the HYBA API key. "+
				"Set the api_key value in the configuration or use the HYBA_API_KEY environment variable.",
		)
	}

	if resp.Diagnostics.HasError() {
		return
	}

	c := client.NewClient(endpoint, apiKey)
	resp.DataSourceData = c
	resp.ResourceData = c
}

func (p *HybaProvider) Resources(ctx context.Context) []func() resource.Resource {
	return []func() resource.Resource{
		NewCiaasServiceResource,
	}
}

func (p *HybaProvider) DataSources(ctx context.Context) []func() datasource.DataSource {
	return []func() datasource.DataSource{
		NewCiaasServiceDataSource,
		NewConnectorsDataSource,
	}
}
