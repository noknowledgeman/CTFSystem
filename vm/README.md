# VM testing environment

This is the VM testing environment that creates a virtual network of vms, each one loaded from one of the samples in the samples directory, each one sharing one base. These vms use qemu and libvirt to function. These commands do not create a subnet (I used virsh default network and dnsmaq for dhcp and dns, with the nat being configured in the deploy and build scripts) for you, and these are most likely all specific to my computer so it is not made with a goal to reproduce but to document how it was run.

The base image used was: [https://cloud.debian.org/images/cloud/trixie/20260512-2476/debian-13-generic-amd64-20260512-2476.qcow2](debian). it was set up with:

```bash
sudo ./customize.sh
```

To build the vms you can use:

```bash
sudo ./build.sh
```

This will create the image for each sample and will pull and build the docker images inside of them.

To run the vms you can then use:

```bash
sudo ./deploy.sh
```

This also places the map of group id (in this case sampleN) to ip addres automaticallyy into the .env so that you can then startup the validation service

To then kill and clean up you can use either action independently:

```bash
sudo ./cleanup.sh shutdown   # kill running QEMU VMs (leaves disks intact)
sudo ./cleanup.sh images     # remove VM disk images (.qcow2)
```

Furthermore, to run a specific vm you can do:

```bash
sudo ./run-vm.sh
```
