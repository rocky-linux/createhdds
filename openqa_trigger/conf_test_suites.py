def default_install_cb(flavor):
    """Figure out the correct test case name for a default_boot_and_
    install pass for a given flavor.
    """
    (payload, imagetype) = flavor.split('_')
    imagetype = imagetype.replace('boot', 'netinst')
    imagetype = imagetype.replace('dvd', 'offline')
    return "{0} {1}".format(payload, imagetype)

TESTCASES = {
    "QA:Testcase_Boot_default_install": {
        "name_cb": default_install_cb,
        "section": 'Default boot and install',
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_install_to_VirtIO": {
        "section": "Storage devices",
        "env": "x86",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_empty": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_User_Interface_Graphical": {
        "section": "User interface",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_user_creation": {
        "section": "Miscellaneous",
        "env": "x86",
        "type": "Installation",
    },
    "QA:Testcase_install_to_PATA": {
        "section": "Storage devices",
        "env": "x86",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_delete_all": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_install_to_SATA": {
        "section": "Storage devices",
        "env": "x86",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_multi_select": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_install_to_SCSI": {
        "section": "Storage devices",
        "env": "x86",
        "type": "Installation",
    },
    "QA:Testcase_Anaconda_updates.img_via_URL": {
        "section": "Miscellaneous",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_kickstart_user_creation": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_Http_Server_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_Mirrorlist_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_HTTP/FTP_graphical": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_install_repository_HTTP/FTP_variation": {
        "section": "Installation repositories",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_Package_Sets_Minimal_Package_Install": {
        "section": "Package sets",
        "env": "$RUNARCH$",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_encrypted": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_delete_partial": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_free_space": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_partitioning_guided_multi_empty_all": {
        "section": "Guided storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_Partitioning_On_Software_RAID": {
        "section": "Custom storage configuration",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    "QA:Testcase_Kickstart_Hd_Device_Path_Ks_Cfg": {
        "section": "Kickstart",
        "env": "Result",
        "type": "Installation",
    },
    "QA:Testcase_upgrade_fedup_cli_previous_minimal": {
        "section": "Upgrade",
        "env": "x86 BIOS",
        "type": "Installation",
    },
    #        "": {
    # "name_cb": callbackfunc # optional, called with 'flavor'
    #            "section": "",
    #            "env": "x86",
    #            "type": "Installation",
    #            },
}


TESTSUITES = {
    "default_install": [
        "QA:Testcase_Boot_default_install",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        ],
    "package_set_minimal": [
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_delete_pata": [
        "QA:Testcase_install_to_PATA",
        "QA:Testcase_partitioning_guided_delete_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_sata_multi": [
        "QA:Testcase_install_to_SATA",
        "QA:Testcase_partitioning_guided_multi_select",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_scsi_updates_img": [
        "QA:Testcase_install_to_SCSI",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_updates.img_via_URL",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_kickstart_user_creation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Http_Server_Ks_Cfg",
        ],
    "server_mirrorlist_graphical": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_Mirrorlist_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_repository_http_graphical": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_repository_http_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_mirrorlist_http_variation": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_simple_encrypted": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        ],
    "server_delete_partial": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_delete_partial",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_simple_free_space": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_free_space",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_multi_empty": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_multi_empty_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_software_raid": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Partitioning_On_Software_RAID",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_kickstart_hdd": [
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Hd_Device_Path_Ks_Cfg",
        ],
    "fedup_minimal": [
        "QA:Testcase_upgrade_fedup_cli_previous_minimal",
        ],
    }
