package main

import (
	"context"
	"flag"
	"log"

	"github.com/hashicorp/terraform-plugin-framework/providerserver"
	"hyba-ai/terraform-provider-hyba/internal/provider"
)

var (
	version string = "1.0.0"
)

func main() {
	var debug bool

	opts := providerserver.ServeOpts{
		Address: "registry.terraform.io/hyba-ai/hyba",
		Debug:   debug,
	}

	flag.BoolVar(&debug, "debug", false, "set to true to run the provider with support for debuggers like delve")
	flag.Parse()

	err := providerserver.Serve(context.Background(), provider.New(version), opts)
	if err != nil {
		log.Fatal(err)
	}
}
