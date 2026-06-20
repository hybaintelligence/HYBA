package provider

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/datasource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"hyba-ai/terraform-provider-hyba/internal/client"
)

var (
	_ datasource.DataSource = &ConnectorsDataSource{}
)

func NewConnectorsDataSource() datasource.DataSource {
	return &ConnectorsDataSource{}
}

type ConnectorsDataSource struct {
	client *client.Client
}

type ConnectorsDataSourceModel struct {
	Connectors types.Map `tfsdk:"connectors"`
}

type ConnectorInfo struct {
	Type        string `tfsdk:"type"`
	Description string `tfsdk:"description"`
	Version     string `tfsdk:"version"`
	Status      string `tfsdk:"status"`
}

func (d *ConnectorsDataSource) Metadata(ctx context.Context, req datasource.MetadataRequest, resp *datasource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_connectors"
}

func (d *ConnectorsDataSource) Schema(ctx context.Context, req datasource.SchemaRequest, resp *datasource.SchemaResponse) {
	resp.Schema = schema.Schema{
		MarkdownDescription: "List available HYBA connectors.",
		Attributes: map[string]schema.Attribute{
			"connectors": schema.MapAttribute{
				Computed:            true,
				ElementType:         types.StringType,
				MarkdownDescription: "Map of available connectors",
			},
		},
	}
}

func (d *ConnectorsDataSource) Configure(ctx context.Context, req datasource.ConfigureRequest, resp *datasource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}

	client, ok := req.ProviderData.(*client.Client)
	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected DataSource Configure Type",
			fmt.Sprintf("Expected *client.Client, got: %T. Please report this issue to the provider developers.", req.ProviderData),
		)
		return
	}

	d.client = client
}

func (d *ConnectorsDataSource) Read(ctx context.Context, req datasource.ReadRequest, resp *datasource.ReadResponse) {
	connectors, err := d.client.ListConnectors(ctx)
	if err != nil {
		resp.Diagnostics.AddError("Error listing connectors", err.Error())
		return
	}

	// Convert connectors map to Terraform types
	connectorsMap := make(map[string]types.String)
	for key, value := range connectors {
		// Convert value to string representation
		if strVal, ok := value.(string); ok {
			connectorsMap[key] = types.StringValue(strVal)
		} else {
			// Try to marshal as JSON for complex types
			connectorsMap[key] = types.StringValue(fmt.Sprintf("%v", value))
		}
	}

	connectorsValue, diags := types.MapValueFrom(ctx, types.StringType, connectorsMap)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	state := &ConnectorsDataSourceModel{
		Connectors: connectorsValue,
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, state)...)
}
