"""Policy API."""
from panos.policies import PreRulebase, PostRulebase, SecurityRule
from panos.panorama import DeviceGroup

from .base import BaseAPI


class PanoramaPolicy(BaseAPI):
    """Policy Objects API SDK."""

    policies = {}
    _rulebase = {"PRE": PreRulebase, "POST": PostRulebase}

    def _delete_instance(self, name, location):
        """Deletes an instance of an PreRulebase or PostRulebase."""
        obj = self.policies[name].pop(location)
        obj.delete()

    def get_rulebase(self, location, pre_post):
        """Returns a prefetched instance."""
        if location == self.pano:
            location = self.pano
            loc_name = "shared"
        elif isinstance(location, str):
            location = self.device_groups[location]
            loc_name = location.name
        elif isinstance(location, DeviceGroup):
            loc_name = location.name
        else:
            raise ValueError("Invalid location provided")
        return self.policies[loc_name][pre_post], loc_name

    def get_security_rule(self, rulebase, rulename):  # pylint: disable=no-self-use
        """Returns a rule by name from rulebase."""
        for rule in rulebase[0].children:
            if isinstance(rule, SecurityRule) and rule.name == rulename:
                return rule
        raise ValueError("Unable to find SecurityRule.")

    #####################
    # (Pre/Post)Rulebase
    #####################

    def create_security_rule(self, location, pre_post, name, **kwargs):
        """Create SecurityRule."""
        rulebase, loc_name = self.get_rulebase(location, pre_post)
        rulebase = rulebase[0]
        location.add(rulebase)
        rule = SecurityRule(name, **kwargs)
        rulebase.add(rule)
        rule.create()
        # self.policies[loc_name][pre_post] = rulebase.refreshall()
        return rule

    def retrieve_security_rules(self):
        """Returns a dictionary with the location at the parent key and rules as values."""
        self.policies = {dg: {} for dg in self.device_groups.keys()}
        self.policies["shared"] = {}
        self.policies["shared"]["PRE"] = PreRulebase.refreshall(self.pano)
        self.policies["shared"]["POST"] = PostRulebase.refreshall(self.pano)
        for name, dev_group in self.device_groups.items():
            self.policies[name]["PRE"] = PreRulebase.refreshall(dev_group)
            self.policies[name]["POST"] = PostRulebase.refreshall(dev_group)
        return self.policies

    def update_security_rule(self, location, pre_post, name, **kwargs):
        """Update a SecurityRule."""
        rulebase, loc_name = self.get_rulebase(location, pre_post)
        rule = self.get_security_rule(rulebase, name)
        for attr, value in kwargs.items():
            if hasattr(rule, attr):
                setattr(rule, attr, value)
            else:
                raise ValueError(f"Unsupported attribute {attr}")
        rule.apply()
        # self.policies[loc_name][pre_post] = rulebase.refreshall()
        return rule

    def delete_security_rule(self, location, pre_post, name):
        """Delete a SecurityRule."""
        rulebase, loc_name = self.get_rulebase(location, pre_post)
        rule = self.get_security_rule(rulebase, name)
        rule.delete()
        self.policies[loc_name][pre_post] = rulebase.refreshall()
        return rule
