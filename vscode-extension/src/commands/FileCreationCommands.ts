import * as vscode from 'vscode';
import * as path from 'path';

const IP_CORE_TEMPLATE = `apiVersion: 1.0
vlnv:
  vendor: my_vendor
  library: my_library
  name: New_IP_Core
  version: 1.0.0

description: A new IP Core definition

# Location of the reusable bus library
useBusLibrary: common/bus_definitions.yml

# Top-level clock definitions
clocks: []

# Top-level reset definitions
resets: []

# Bus interfaces
busInterfaces: []

# Parameters
parameters: []
`;

const MEMORY_MAP_TEMPLATE = `schemaVersion: 1.0.0
addressBlocks:
  - name: Default_Block
    baseAddress: 0x00000000
    range: 4096
    width: 32
    usage: register
    access: read-write
    description: Default address block
    registers:
      - name: CTRL
        addressOffset: 0x0
        size: 32
        access: read-write
        description: Control register
        fields: []
`;

export async function createIpCoreCommand(): Promise<void> {
    await createFileWithTemplate('new_ip_core.yml', IP_CORE_TEMPLATE);
}

export async function createMemoryMapCommand(): Promise<void> {
    await createFileWithTemplate('new_memory_map.memmap.yml', MEMORY_MAP_TEMPLATE);
}

async function createFileWithTemplate(defaultFileName: string, template: string): Promise<void> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let defaultUri: vscode.Uri | undefined;

    if (workspaceFolders && workspaceFolders.length > 0) {
        defaultUri = vscode.Uri.joinPath(workspaceFolders[0].uri, defaultFileName);
    }

    const uri = await vscode.window.showSaveDialog({
        defaultUri,
        saveLabel: 'Create File',
        title: `Create ${defaultFileName}`,
        filters: {
            'YAML Files': ['yml', 'yaml']
        }
    });

    if (uri) {
        try {
            await vscode.workspace.fs.writeFile(uri, new Uint8Array(Buffer.from(template)));
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to create file: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
}
