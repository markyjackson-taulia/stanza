__author__ = 'victor'
from collections import OrderedDict
import random


class InvalidFieldsException(Exception):
    pass


class Dataset(object):
    """
    Generic Dataset object that encapsulates a list of instances.

    The dataset stores the instances in an
    ordered dictionary of fields. Each field maps to a list, the ith element of the list for field 'foo'
    corresponds to the attribute 'foo' for the ith instance in the dataset.

    The dataset object supports indexing, iterating, slicing (eg. for iterating over batches), shuffling,
    conversion to/from CONLL format, among others.
    """

    def __init__(self, fields):
        """
        :param fields: An ordered dictionary in which a key is the name of an attribute and a value is a list of the values of the instances in the dataset.
        :return: A Dataset object
        """
        self.fields = OrderedDict(fields)
        length = None
        length_field = None
        for name, d in fields.items():
            if length is None:
                length = len(d)
                length_field = name
            else:
                if len(d) != length:
                    raise InvalidFieldsException('field {} has length {} but field {} has length {}'.format(length_field, length, name, len(d)))

    def __len__(self):
        """
        :return: The number of instances in the dataset.
        """
        if len(self.fields) == 0:
            return 0
        return len(self.fields.values()[0])

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join(self.fields.keys()))

    @classmethod
    def load_conll(cls, fname):
        """
        The CONLL file must have a tab delimited header, for example:

        ```
        # Name  SSN
        Alice   12345
        Bob     123
        ```

        :param fname: The CONLL formatted file from which to load the dataset
        :return: loaded Dataset instance
        """
        with open(fname) as f:
            header = f.next().strip().split('\t')
            header[0] = header[0].lstrip('# ')
            fields = OrderedDict([(head, []) for head in header])
            for line in f:
                if not line.strip():
                    continue
                rows = [None if e == '-' else e for e in line.strip().split('\t')]
                for i, k in enumerate(fields.keys()):
                    fields[k].append(rows[i])
        return cls(fields)

    def write_conll(self, fname):
        """
        Serializes the dataset in CONLL format to fname
        """
        with open(fname, 'wb') as f:
            f.write('# {}\n'.format('\t'.join(self.fields.keys())))
            for i, d in enumerate(self):
                line = '\t'.join(['-' if v is None else str(v) for v in d.values()])
                if i != len(self) - 1:
                    line += '\n'
                f.write(line)

    def convert(self, converters, in_place=False):
        """
        Applies transformations to the dataset.
        :param converters: A dictionary specifying the function to apply to each field. If a field is missing from the dictionary, then it will not be transformed.
        :param in_place: Whether to perform the transformation in place or create a new dataset instance
        :return: the transformed dataset instance
        """
        dataset = self if in_place else self.__class__(OrderedDict([(name, data[:]) for name, data in self.fields.items()]))
        for name, convert in converters.items():
            if name not in self.fields.keys():
                raise InvalidFieldsException('Converter specified for non-existent field {}'.format(name))
            for i, d in enumerate(dataset.fields[name]):
                dataset.fields[name][i] = convert(d)
        return dataset

    def shuffle(self):
        """
        Re-indexes the dataset in random order
        :return: the shuffled dataset instance
        """
        order = range(len(self))
        random.shuffle(order)
        for name, data in self.fields.items():
            reindexed = []
            for _, i in enumerate(order):
                reindexed.append(data[i])
            self.fields[name] = reindexed
        return self

    def __getitem__(self, item):
        """
        :param item: An integer index or a slice (eg. 2, 1:, 1:5)
        :return: an ordered dictionary of the instance(s) at index/indices `item`.
        """
        return OrderedDict([(name, data[item]) for name, data in self.fields.items()])

    def __setitem__(self, key, value):
        """
        :param key: An integer index or a slice (eg. 2, 1:, 1:5)
        :param value: Sets the instances at index/indices `key` to the instances(s) `value`
        """
        for name, data in self.fields.items():
            if name not in value:
                raise InvalidFieldsException('field {} is missing in input data: {}'.format(name, value))
            data[key] = value[name]

    def __iter__(self):
        """
        :return: A iterator over the instances in the dataset
        """
        for i in xrange(len(self)):
            yield self[i]

    def copy(self):
        """
        :return: A deep copy of the dataset (each instance is copied).
        """
        return self.__class__(OrderedDict([(name, data[:]) for name, data in self.fields.items()]))
