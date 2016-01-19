Odoo NTTY
---------

Handle your produtcs with ease, by integrating with <a href="https://www.ntty.com">NTTY, where your produtcs live</a>

<a href="https://www.odoo.com/page/ntty">Open Source NTTY Module</a>.

Import entties and transform them into products. Use the settings to define
your way of dealing with products, their attriubtes and their Suppliers.
Always keep your products up to date, through lifecycle manangement.

NTTY Import with ease
---------------------

Use the NTTY Import wizard to import your entities from NTTY and transform
them into Products in Odoo. The wizard uses the entity identifier, to gather
the entity information, such as, name, product owner, values etc. Depending
on your settings and the entity itself, a supplier list will be rendered
and one product will be created pr supplier. 


Keep your products up to date
-----------------------------

By invoking the Product Lifcycle Management module, you will be able to track
the status of your product. It will be synced with NTTY's own lifecycle , through
running a background job

Import Customers/companies
--------------------------

If desired, you can import your customers based on how you have defined your
entity in NTTY. This will also run as a bacground job, based on your settings.

NTTY Configuration
------------------

Since entity retrieval will be done thorugh API calls to NTTY, we need configure
the connection. You will be required to enter:
- Ntty service address: ** http://www.ntty.com/api/v1/ **
- NTTY service user email: ** email address of the NTTY user ** 
- NTTY service token: ** the authorization token of the NTTY user ** 

User specific settings
----------------------

There are numerous user specifc settings that can be set.

## Product settings

Here we will list the settings that can be issued for a product

## Product variants settings

Here we will outline how to access and populate the attributes that are defined
as values on the entity

## Lifecycle settings

Here we will list the settings that can be issued for liefecycle


Dependencies
------------

The NTTY Module is dependent on the Product Brand Module, Product Variants and
the Product Lifecycle Managment module
