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
	_ datasource.DataSource = &CiaasServiceDataSource{}
)

func NewCiaasServiceDataSource() datasource.DataSource {
	return &CiaasServiceDataSource{}
}

type CiaasServiceDataSource struct {
	client *client.Client
}

type CiaasServiceDataSourceModel struct {
	ID               types.String `tfsdk:"id"`
	Name             types.String `tfsdk:"name"`
	Tier             types.String `tfsdk:"tier"`
	State            types.String `tfsdk:"state"`
	Tenancy          types.String `tfsdk:"tenancy"`
	Owner            types.String `tfsdk:"owner"`
	CreatedAt        types.String `tfsdk:"created_at"`
	UpdatedAt        types.String `tfsdk:"updated_at"`
	EvidenceSeal     types.String `tfsdk:"evidence_seal"`
	ClaimBoundary    types.String `tfsdk:"claim_boundary"`
}

func (d *CiaasServiceDataSource) Metadata(ctx context.Context, req datasource.MetadataRequest, resp *datasource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_ciaas_service"
}

func (d *CiaasServiceDataSource) Schema(ctx context.Context, req datasource.SchemaRequest, resp *datasource.SchemaResponse) {
	resp.Schema = schema.Schema{
		MarkdownDescription: "Fetch a HYBA Computational Intelligence Service by ID.",
		Attributes: map[string]schema.Attribute{
			"id": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "Service ID",
			},
			"name": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Service name",
			},
			"tier": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Service tier",
			},
			"state": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Current service state",
			},
			"tenancy": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Tenancy mode",
			},
			"owner": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Service owner",
			},
			"created_at": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Creation timestamp",
			},
			"updated_at": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Last update timestamp",
			},
			"evidence_seal": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Evidence seal for cryptographic verification",
			},
			"claim_boundary": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Claim boundary documentation",
			},
		},
	}
}

func (d *CiaasServiceDataSource) Configure(ctx context.Context, req datasource.ConfigureRequest, resp *datasource.ConfigureResponse) {
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

func (d *CiaasServiceDataSource) Read(ctx context.Context, req datasource.ReadRequest, resp *datasource.ReadResponse) {
	var config CiaasServiceDataSourceModel

	resp.Diagnostics.Append(req.Config.Get(ctx, &config)...)
	if resp.Diagnostics.HasError() {
		return
	}

	service, err := d.client.GetService(ctx, config.ID.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Error reading service", err.Error())
		return
	}

	state := &CiaasServiceDataSourceModel{
		ID:            types.StringValue(service.ID),
		Name:          types.StringValue(service.Name),
		Tier:          types.StringValue(service.Tier),
		State:         types.StringValue(service.State),
		Tenancy:       types.StringValue(service.Tenancy),
		Owner:         types.StringValue(service.Owner),
		CreatedAt:     types.StringValue(service.CreatedAt),
		UpdatedAt:     types.StringValue(service.UpdatedAt),
		EvidenceSeal:  types.StringValue(service.EvidenceSeal),
		ClaimBoundary: types.StringValue(service.ClaimBoundary),
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, state)...)
}
